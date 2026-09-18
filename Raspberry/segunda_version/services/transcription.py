# services/transcription.py
#
# Estrategia:
#   1. Intenta transcribir con Groq Whisper (online, ~10x más rápido)
#   2. Si falla (sin internet, error de API, timeout), cae a Whisper local
#
# El modelo local se carga en memoria solo cuando se necesita por primera vez
# (lazy loading), para no penalizar el arranque si la conexión está disponible.

import io
import time
import socket
import numpy as np
import soundfile as sf
import torch
from typing import Optional, Dict

# ─────────────────────────────────────────────────────────────────────────────
# UTILIDAD: chequeo de conectividad
# ─────────────────────────────────────────────────────────────────────────────

def _hay_internet(host: str = "8.8.8.8", puerto: int = 53, timeout: float = 1.5) -> bool:
    """Prueba rápida de conectividad TCP. No hace HTTP, es instantáneo."""
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, puerto))
        return True
    except OSError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# BACKEND LOCAL — Whisper en CPU/GPU
# ─────────────────────────────────────────────────────────────────────────────

class _BackendLocal:
    """Carga el modelo Whisper localmente. Se instancia de forma lazy."""

    def __init__(self, modelo: str, idioma: str, dispositivo: Optional[str]):
        import whisper  # import local para no romper si no está instalado

        if dispositivo is None:
            dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
        self.dispositivo = dispositivo
        self.idioma      = idioma

        print(f"   📦 Cargando Whisper local '{modelo}' en {dispositivo}...")
        t0 = time.time()
        self.modelo = whisper.load_model(modelo, device=dispositivo)
        print(f"   ✅ Whisper local listo ({time.time()-t0:.1f}s)")

    def transcribir(self, audio: np.ndarray, sample_rate: int) -> Dict:
        import whisper

        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        if np.max(np.abs(audio)) > 1.0:
            audio = audio / np.max(np.abs(audio))

        resultado = self.modelo.transcribe(
            audio,
            language=self.idioma,
            fp16=(self.dispositivo == "cuda")
        )
        return {
            "texto":     resultado["text"].strip(),
            "idioma":    resultado["language"],
            "segmentos": resultado.get("segments", []),
            "backend":   "local"
        }


# ─────────────────────────────────────────────────────────────────────────────
# BACKEND ONLINE — Groq Whisper API
# ─────────────────────────────────────────────────────────────────────────────

class _BackendGroq:
    """Usa la API de Groq para transcribir. Requiere groq instalado y API key."""

    # Modelo más rápido de Groq para STT
    MODELO_STT = "whisper-large-v3-turbo"

    def __init__(self, api_key: str, idioma: str):
        from groq import Groq  # import local

        self.cliente = Groq(api_key=api_key)
        self.idioma  = idioma
        print(f"   🌐 Backend Groq STT listo (modelo: {self.MODELO_STT})")

    def transcribir(self, audio: np.ndarray, sample_rate: int) -> Dict:
        """Convierte el array numpy a WAV en memoria y lo envía a Groq."""
        # Convertir numpy → bytes WAV en memoria (sin tocar disco)
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
        buffer.seek(0)
        buffer.name = "audio.wav"   # Groq SDK necesita el atributo name

        respuesta = self.cliente.audio.transcriptions.create(
            file=buffer,
            model=self.MODELO_STT,
            language=self.idioma,
            response_format="verbose_json"
        )

        # verbose_json devuelve un objeto con .text y .language
        texto  = getattr(respuesta, "text",     "").strip()
        idioma = getattr(respuesta, "language", self.idioma)

        return {
            "texto":     texto,
            "idioma":    idioma,
            "segmentos": [],
            "backend":   "groq"
        }


# ─────────────────────────────────────────────────────────────────────────────
# SERVICIO PRINCIPAL — orquesta online/local con fallback
# ─────────────────────────────────────────────────────────────────────────────

class ServicioTranscripcion:
    """
    Transcripción con fallback automático:
      • Online  → Groq Whisper API   (rápido, requiere internet + GROQ_API_KEY)
      • Offline → Whisper local      (lento, siempre disponible)

    El modelo local se carga en memoria solo la primera vez que se necesita.
    """

    def __init__(self,
                 modelo_local: str = "base",
                 dispositivo: Optional[str] = None,
                 idioma: str = "es",
                 groq_api_key: Optional[str] = None,
                 intentos_online: int = 2,
                 timeout_reintento: float = 30.0):
        """
        Args:
            modelo_local:       Tamaño del modelo Whisper local ('tiny','base','small','medium','large').
            dispositivo:        'cuda' o 'cpu'. None = autodetectar.
            idioma:             Código de idioma para ambos backends.
            groq_api_key:       API key de Groq. Si es None, solo se usa el backend local.
            intentos_online:    Cuántos errores online consecutivos antes de desactivar
                                temporalmente el backend online.
            timeout_reintento:  Segundos antes de volver a intentar el backend online
                                tras desactivarlo temporalmente.
        """
        self.idioma          = idioma
        self.modelo_local_id = modelo_local
        self.dispositivo     = dispositivo
        self.groq_api_key    = groq_api_key

        self._intentos_online_max  = intentos_online
        self._timeout_reintento    = timeout_reintento

        # Estado del circuit-breaker para el backend online
        self._errores_online_consecutivos = 0
        self._online_desactivado_hasta: float = 0.0  # timestamp

        # Backends (lazy)
        self._backend_groq:  Optional[_BackendGroq]  = None
        self._backend_local: Optional[_BackendLocal] = None

        # Inicializar backend Groq si hay API key
        if groq_api_key:
            try:
                self._backend_groq = _BackendGroq(groq_api_key, idioma)
            except Exception as e:
                print(f"⚠️  No se pudo inicializar backend Groq STT: {e}")
                self._backend_groq = None
        else:
            print("   ℹ️  Sin GROQ_API_KEY → solo Whisper local")

        print(f"🎙️  ServicioTranscripcion listo "
              f"({'online+local' if self._backend_groq else 'solo local'})")

    # ── API pública ───────────────────────────────────────────────────────────

    def transcribir(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict:
        """
        Transcribe audio. Intenta online primero; cae a local si falla.

        Returns:
            Dict con claves: texto, idioma, segmentos, backend ('groq'|'local')
        """
        if self._puede_usar_online():
            resultado = self._intentar_online(audio, sample_rate)
            if resultado is not None:
                self._errores_online_consecutivos = 0   # reset circuit-breaker
                return resultado

        # Fallback local
        return self._usar_local(audio, sample_rate)

    def transcribir_rapido(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Versión simplificada que solo retorna el texto."""
        return self.transcribir(audio, sample_rate).get("texto", "")

    # ── Circuit-breaker ───────────────────────────────────────────────────────

    def _puede_usar_online(self) -> bool:
        """True si el backend online está disponible y hay internet."""
        if self._backend_groq is None:
            return False
        if time.time() < self._online_desactivado_hasta:
            return False    # en periodo de espera
        return _hay_internet()

    def _registrar_error_online(self):
        self._errores_online_consecutivos += 1
        if self._errores_online_consecutivos >= self._intentos_online_max:
            self._online_desactivado_hasta = time.time() + self._timeout_reintento
            print(f"⚠️  Backend online desactivado temporalmente "
                  f"({self._timeout_reintento:.0f}s de espera)")

    # ── Backends ──────────────────────────────────────────────────────────────

    def _intentar_online(self, audio: np.ndarray, sample_rate: int) -> Optional[Dict]:
        t0 = time.time()
        try:
            resultado = self._backend_groq.transcribir(audio, sample_rate)
            dt = time.time() - t0
            print(f"   🌐 Groq STT: '{resultado['texto']}' ({dt:.2f}s)")
            return resultado
        except Exception as e:
            self._registrar_error_online()
            print(f"⚠️  Error backend Groq STT: {e} — usando Whisper local")
            return None

    def _usar_local(self, audio: np.ndarray, sample_rate: int) -> Dict:
        # Carga lazy: solo la primera vez que hace falta
        if self._backend_local is None:
            print("📦 Cargando Whisper local por primera vez...")
            self._backend_local = _BackendLocal(
                self.modelo_local_id, self.idioma, self.dispositivo
            )
        t0 = time.time()
        try:
            resultado = self._backend_local.transcribir(audio, sample_rate)
            dt = time.time() - t0
            print(f"   💻 Whisper local: '{resultado['texto']}' ({dt:.2f}s)")
            return resultado
        except Exception as e:
            print(f"❌ Error Whisper local: {e}")
            return {"texto": "", "idioma": self.idioma, "segmentos": [], "backend": "error"}