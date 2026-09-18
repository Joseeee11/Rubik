# services/tts.py
#
# Responsabilidad: convertir texto a voz y coordinar en paralelo:
#   1. Reproducción de audio (pygame)
#   2. Movimiento de mandíbula sincronizado con el volumen del audio
#   3. Cambio de expresiones faciales según marcadores emocionales en el texto
#
# Mantiene esta clase independiente de ia_groq.py — se inyecta como dependencia.
#
# ── DEPENDENCIAS ─────────────────────────────────────────────────────────────
#   pip install groq pygame numpy soundfile
#
# ── FLUJO ────────────────────────────────────────────────────────────────────
#   hablar(texto, segmentos) →
#     [hilo A] reproduce audio por fragmentos
#     [hilo B] lee amplitud de cada chunk → mueve mandíbula
#     [hilo C] espera timestamps → cambia expresión

import io
import re
import time
import threading
import queue
import numpy as np
import soundfile as sf
import pygame

from typing import Optional, Callable, List, Dict


# =============================================================================
# MARCADORES EMOCIONALES
# Zoé puede recibir texto con marcadores [EMOCION] intercalados.
# El LLM los inserta para indicar cuándo cambiar de expresión mientras habla.
# =============================================================================

# Regex que detecta [EMOCION] o [emocion] en el texto
_RE_MARCADOR = re.compile(r"\[(\w+)\]")

def extraer_segmentos(texto_con_marcadores: str) -> tuple[str, List[Dict]]:
    """
    Separa el texto limpio de los marcadores emocionales.

    Entrada:  "Hola! [feliz] Me alegra verte. [curiosa] ¿Qué tal estás?"
    Salida:   ("Hola! Me alegra verte. ¿Qué tal estás?",
               [{"emocion": "feliz",   "char_pos": 6},
                {"emocion": "curiosa", "char_pos": 26}])

    Los char_pos apuntan a la posición en el texto LIMPIO (sin marcadores),
    lo que permite estimar el timestamp aproximado en el audio.
    """
    segmentos = []
    texto_limpio = ""
    cursor = 0

    for match in _RE_MARCADOR.finditer(texto_con_marcadores):
        # Añadir texto antes del marcador
        texto_limpio += texto_con_marcadores[cursor:match.start()]
        segmentos.append({
            "emocion":  match.group(1).lower(),
            "char_pos": len(texto_limpio),   # posición en el texto ya limpio
        })
        cursor = match.end()

    texto_limpio += texto_con_marcadores[cursor:]
    return texto_limpio.strip(), segmentos


def estimar_timestamps(texto: str, duracion_total_s: float, segmentos: List[Dict]) -> List[Dict]:
    """
    Convierte posiciones de carácter a timestamps en segundos,
    asumiendo velocidad de locución uniforme.

    Devuelve los segmentos con el campo 'tiempo_s' añadido.
    """
    n_chars = max(len(texto), 1)
    for seg in segmentos:
        seg["tiempo_s"] = (seg["char_pos"] / n_chars) * duracion_total_s
    return segmentos


# =============================================================================
# SERVICIO TTS
# =============================================================================

class ServicioTTS:
    """
    Text-to-Speech con sincronía física para Zoé.

    Usa Groq TTS (online) con fallback a pyttsx3 (offline/local).
    Coordina movimiento de mandíbula y cambio de expresiones mientras habla.
    """

    # Groq TTS — modelos disponibles
    MODELO_TTS        = "canopylabs/orpheus-v1-english"
    VOZ_DEFAULT       = "troy"   # voz femenina en español

    # Parámetros de sincronía de mandíbula
    _CHUNK_MS         = 40      # ms por chunk de análisis de amplitud
    _ANGULO_MIN_BOCA  = 0       # mandíbula cerrada
    _ANGULO_MAX_BOCA  = 120      # apertura máxima (según caraFases.py)
    _SUAVIZADO        = 0.35    # factor de suavizado exponencial (0=brusco, 1=lento)

    def __init__(self,
                 api_key: str,
                 gestor,                         # GestorExpresiones
                 voz: str = VOZ_DEFAULT,
                 volumen: float = 1.0,
                 velocidad: float = 1.0):
        """
        Args:
            api_key:   API key de Groq (misma que para LLM y STT).
            gestor:    Instancia de GestorExpresiones para mover motores.
            voz:       Voz de Groq TTS a usar.
            volumen:   Volumen de reproducción (0.0-1.0).
            velocidad: Multiplicador de velocidad de habla (0.5-2.0, no soportado por todos los motores).
        """
        from groq import Groq
        self.cliente  = Groq(api_key=api_key)
        self.gestor   = gestor
        self.voz      = voz
        self.volumen  = volumen
        self.velocidad = velocidad

        # Estado de control
        self._hablando        = False
        self._detener_flag    = threading.Event()
        self._hilo_habla:     Optional[threading.Thread] = None

        # Inicializar pygame mixer (audio)
        if not pygame.get_init():
            pygame.init()
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)

        print(f"🔊 ServicioTTS listo (voz={voz})")

    # =========================================================================
    # API PÚBLICA
    # =========================================================================

    @property
    def hablando(self) -> bool:
        return self._hablando

    def hablar(self,
               texto_con_marcadores: str,
               bloquear: bool = False) -> None:
        """
        Genera y reproduce el texto.
        Los marcadores [EMOCION] en el texto controlan las expresiones.

        Args:
            texto_con_marcadores: Texto que puede incluir marcadores [emocion].
            bloquear: Si True, bloquea el hilo llamante hasta terminar.
        """
        if not texto_con_marcadores.strip():
            return

        # Cancelar habla anterior si existe
        self.detener()

        self._detener_flag.clear()
        self._hilo_habla = threading.Thread(
            target=self._ciclo_habla,
            args=(texto_con_marcadores,),
            daemon=True
        )
        self._hilo_habla.start()

        if bloquear:
            self._hilo_habla.join()

    def detener(self) -> None:
        """Interrumpe la habla actual inmediatamente."""
        if self._hablando:
            self._detener_flag.set()
            pygame.mixer.stop()
            if self._hilo_habla and self._hilo_habla.is_alive():
                self._hilo_habla.join(timeout=1.0)
            self._hablando = False
            # Cerrar boca al parar
            self._mover_boca(0)

    def cerrar(self) -> None:
        """Libera recursos."""
        self.detener()
        pygame.mixer.quit()

    # =========================================================================
    # CICLO PRINCIPAL DE HABLA (ejecuta en hilo separado)
    # =========================================================================

    def _ciclo_habla(self, texto_con_marcadores: str) -> None:
        self._hablando = True
        try:
            # 1. Separar texto limpio y marcadores emocionales
            texto_limpio, segmentos = extraer_segmentos(texto_con_marcadores)
            print(f"🗣️  TTS: '{texto_limpio[:60]}...' | {len(segmentos)} marcadores")

            # 2. Generar audio con Groq TTS
            audio_bytes = self._generar_audio(texto_limpio)
            if audio_bytes is None or self._detener_flag.is_set():
                return

            # 3. Decodificar a numpy para análisis de amplitud
            audio_np, sample_rate = self._decodificar_audio(audio_bytes)

            # 4. Calcular timestamps de los marcadores emocionales
            duracion_total = len(audio_np) / sample_rate
            segmentos = estimar_timestamps(texto_limpio, duracion_total, segmentos)

            # 5. Lanzar reproducción y sincronía en paralelo
            cola_amplitud = queue.Queue(maxsize=200)

            hilo_repro  = threading.Thread(
                target=self._reproducir_audio,
                args=(audio_bytes, cola_amplitud),
                daemon=True
            )
            hilo_boca   = threading.Thread(
                target=self._sincronizar_boca,
                args=(cola_amplitud,),
                daemon=True
            )
            hilo_expr   = threading.Thread(
                target=self._sincronizar_expresiones,
                args=(segmentos, duracion_total),
                daemon=True
            )

            hilo_repro.start()
            hilo_boca.start()
            hilo_expr.start()

            hilo_repro.join()   # esperar a que termine el audio
            hilo_boca.join(timeout=1.0)
            hilo_expr.join(timeout=1.0)

        except Exception as e:
            print(f"❌ Error en TTS: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._hablando = False
            self._mover_boca(0)   # cerrar boca siempre al terminar
            print("🔇 TTS finalizado")

    # =========================================================================
    # GENERACIÓN DE AUDIO — Groq TTS con fallback local
    # =========================================================================

    def _generar_audio(self, texto: str) -> Optional[bytes]:
        """Llama a Groq TTS y devuelve los bytes de audio (WAV/MP3)."""
        try:
            print(f"   🌐 Groq TTS generando audio...")
            t0 = time.time()
            respuesta = self.cliente.audio.speech.create(
                model=self.MODELO_TTS,
                voice=self.voz,
                input=texto,
                response_format="wav",
            )
            audio_bytes = respuesta.read()
            print(f"   ✅ Audio generado ({time.time()-t0:.2f}s, {len(audio_bytes)//1024}KB)")
            return audio_bytes

        except Exception as e:
            print(f"⚠️  Groq TTS falló: {e} — usando pyttsx3 local")
            return self._generar_audio_local(texto)

    def _generar_audio_local(self, texto: str) -> Optional[bytes]:
        """Fallback: genera audio con pyttsx3 y lo devuelve como bytes WAV."""
        try:
            import pyttsx3
            import tempfile
            import os

            engine = pyttsx3.init()
            engine.setProperty("rate", 150)
            engine.setProperty("volume", self.volumen)

            # Seleccionar voz en español si está disponible
            for v in engine.getProperty("voices"):
                if "es" in v.id.lower() or "spanish" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break

            # Guardar en archivo temporal y leer los bytes
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name

            engine.save_to_file(texto, tmp_path)
            engine.runAndWait()

            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
            os.unlink(tmp_path)

            print(f"   ✅ Audio local generado ({len(audio_bytes)//1024}KB)")
            return audio_bytes

        except Exception as e:
            print(f"❌ pyttsx3 también falló: {e}")
            return None

    # =========================================================================
    # REPRODUCCIÓN DE AUDIO
    # =========================================================================

    def _decodificar_audio(self, audio_bytes: bytes) -> tuple[np.ndarray, int]:
        """Decodifica bytes de audio a array numpy float32."""
        buf = io.BytesIO(audio_bytes)
        audio_np, sample_rate = sf.read(buf, dtype="float32")
        if audio_np.ndim > 1:
            audio_np = audio_np.mean(axis=1)   # stereo → mono
        return audio_np, sample_rate

    def _reproducir_audio(self, audio_bytes: bytes, cola_amplitud: queue.Queue) -> None:
        """
        Reproduce el audio con pygame y, en paralelo, alimenta la cola
        con la amplitud de cada chunk para que _sincronizar_boca() la consuma.
        """
        try:
            # Decodificar para análisis de amplitud
            audio_np, sample_rate = self._decodificar_audio(audio_bytes)
            chunk_samples = int(sample_rate * self._CHUNK_MS / 1000)

            # Calcular amplitud por chunks y encolar ANTES de reproducir
            # (la reproducción y el análisis van a la misma velocidad real)
            for i in range(0, len(audio_np), chunk_samples):
                chunk = audio_np[i:i + chunk_samples]
                amplitud = float(np.sqrt(np.mean(chunk ** 2)))   # RMS
                try:
                    cola_amplitud.put_nowait(amplitud)
                except queue.Full:
                    pass   # si la cola está llena, descartamos este chunk

            cola_amplitud.put(None)   # señal de fin

            # Reproducir con pygame
            sound = pygame.mixer.Sound(io.BytesIO(audio_bytes))
            sound.set_volume(self.volumen)
            channel = sound.play()

            # Esperar a que termine o se interrumpa
            while channel and channel.get_busy():
                if self._detener_flag.is_set():
                    channel.stop()
                    break
                time.sleep(0.02)

        except Exception as e:
            print(f"❌ Error en reproducción: {e}")
            cola_amplitud.put(None)

    # =========================================================================
    # SINCRONÍA DE BOCA
    # =========================================================================

    def _sincronizar_boca(self, cola_amplitud: queue.Queue) -> None:
        """
        Consume amplitudes de la cola y mueve la mandíbula en consecuencia.
        Usa suavizado exponencial para que el movimiento sea fluido.
        """
        angulo_actual = 0.0
        intervalo = self._CHUNK_MS / 1000.0

        while not self._detener_flag.is_set():
            try:
                amplitud = cola_amplitud.get(timeout=0.5)
            except queue.Empty:
                continue

            if amplitud is None:   # señal de fin
                break

            # Normalizar amplitud a [0, 1] (empírico: voz normal ≈ 0.05-0.3 RMS)
            ratio = min(amplitud / 0.25, 1.0)

            # Ángulo objetivo
            angulo_objetivo = self._ANGULO_MIN_BOCA + ratio * (self._ANGULO_MAX_BOCA - self._ANGULO_MIN_BOCA)

            # Suavizado exponencial
            angulo_actual = (self._SUAVIZADO * angulo_actual +
                             (1 - self._SUAVIZADO) * angulo_objetivo)

            self._mover_boca(int(angulo_actual))
            time.sleep(intervalo)

        # Cerrar boca al terminar
        self._mover_boca(0)

    def _mover_boca(self, angulo: int) -> None:
        """Mueve la mandíbula al ángulo indicado (0-40°)."""
        try:
            from utils.expresiones import M_MANDIBULA
            self.gestor.enviar_motor(M_MANDIBULA, max(0, min(40, angulo)))
        except Exception:
            pass

    # =========================================================================
    # SINCRONÍA DE EXPRESIONES
    # =========================================================================

    def _sincronizar_expresiones(self,
                                  segmentos: List[Dict],
                                  duracion_total: float) -> None:
        """
        Aplica expresiones en los timestamps calculados mientras suena el audio.
        """
        if not segmentos:
            return

        t_inicio = time.time()

        # Diccionario de rescate: Traduce alucinaciones comunes a expresiones reales
        sinonimos_ia = {
            "enojado": "enojada",
            "furioso": "enojada",
            "furiosa": "enojada",
            "molesta": "enojada",
            "contento": "feliz",
            "contenta": "feliz",
            "alegre": "feliz",
            "pausa": "neutral",
            "silencio": "neutral",
            "pensando": "curiosa",
            "sorprendido": "sorprendida",
            "asustado": "asustada",
            "misterioso": "misteriosa"
        }

        for seg in segmentos:
            if self._detener_flag.is_set():
                break

            tiempo_objetivo = seg["tiempo_s"]
            tiempo_transcurrido = time.time() - t_inicio

            # Esperar hasta el momento correcto
            espera = tiempo_objetivo - tiempo_transcurrido
            if espera > 0:
                # Esperar en trozos pequeños para poder interrumpir
                fin = time.time() + espera
                while time.time() < fin:
                    if self._detener_flag.is_set():
                        return
                    time.sleep(0.02)

            emocion_cruda = seg["emocion"].lower()
            # Traducir la emoción si está en el diccionario de sinónimos, si no, usar la cruda
            emocion_real = sinonimos_ia.get(emocion_cruda, emocion_cruda)

            print(f"   🎭 Expresión en t={tiempo_objetivo:.1f}s: {emocion_real} (original: {emocion_cruda})")
            
            try:
                self.gestor.aplicar_expresion(emocion_real)
            except Exception as e:
                print(f"   ⚠️ Expresión '{emocion_real}' no encontrada: {e}")