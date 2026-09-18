# core/callbacks.py
#
# Responsabilidad ÚNICA: recibir los datos crudos de MediaPipe y audio,
# delegarlos al módulo correcto y decidir qué enviar al ESP32.
#
# Módulos especializados:
#   core/facial.py       → geometría del iris y blendshapes
#   core/expresiones.py  → catálogo de expresiones y GestorExpresiones
#   services/ia_groq.py  → LLM Groq + tool calling

from core.facial import ProcesadorFacial
from utils.expresiones import GestorExpresiones
from services.esp32 import ConexionESP32, NUM_MOTORES
from services.ia_groq import ServicioIA
from services.tts import ServicioTTS


class ProcesadorDeCallbacks:
    """
    Puente entre MediaPipe, MotorDeAudio y el resto del sistema.
    """

    # ── Tabla de motores (alias cortos para uso interno) ──────────────────────
    MOTOR_OJO_IZQ_H    = 1
    MOTOR_OJO_IZQ_V    = 0
    MOTOR_PARP_IZQ_SUP = 2
    MOTOR_PARP_IZQ_INF = 3
    MOTOR_OJO_DER_H    = 5
    MOTOR_OJO_DER_V    = 4
    MOTOR_PARP_DER_SUP = 6
    MOTOR_PARP_DER_INF = 7
    MOTOR_MANDIBULA    = 15

    def __init__(self,
                 estado_robot: dict,
                 esp32_serial: ConexionESP32,
                 groq_api_key: str,
                 groq_modelo: str = "llama-3.3-70b-versatile",
                 tts_voz: str = "diana",
                 tts_volumen: float = 1.0):
        """
        Args:
            estado_robot:   Diccionario compartido con el estado de Zoé.
            esp32_serial:   Instancia de ConexionESP32.
            groq_api_key:   API key de Groq (usada para LLM, STT y TTS).
            groq_modelo:    Modelo Groq a usar para el LLM.
            tts_voz:        Voz de Groq TTS.
            tts_volumen:    Volumen de reproducción (0.0-1.0).
        """
        self.estado = estado_robot
        self.esp32  = esp32_serial

        # Array de posiciones (0-180) compartido por todos los módulos
        self.posiciones: list[int] = [90] * NUM_MOTORES

        # ── Procesadores ──────────────────────────────────────────────────────
        self.facial = ProcesadorFacial()

        # GestorExpresiones: único punto de acceso al ESP32
        self.gestor = GestorExpresiones(
            esp32=esp32_serial,
            posiciones_actuales=self.posiciones
        )

        # TTS: voz de Zoé con sincronía de boca y expresiones
        self.tts = ServicioTTS(
            api_key=groq_api_key,
            gestor=self.gestor,
            voz=tts_voz,
            volumen=tts_volumen
        )

        # ServicioIA: LLM + tool calling + TTS integrado
        self.ia = ServicioIA(
            api_key=groq_api_key,
            gestor=self.gestor,
            tts=self.tts,
            modelo=groq_modelo,
            historial_max=10
        )

    # ==========================================================================
    # CALLBACKS PÚBLICOS — MediaPipe los llama en hilo aparte
    # ==========================================================================

    def recibir_datos_cara(self, result, output_image, timestamp_ms):
        """Callback del FaceLandmarker."""
        if not result.face_landmarks or not result.face_blendshapes:
            return
        landmarks   = result.face_landmarks[0]
        blendshapes = result.face_blendshapes[0]
        resultado = self.facial.procesar(landmarks, blendshapes)
        self._aplicar_resultado_facial(resultado)

    def recibir_datos_pose(self, result, output_image, timestamp_ms):
        """Callback del PoseLandmarker."""
        if not result.pose_landmarks:
            return
        # TODO: self.pose.procesar(result.pose_landmarks[0])

    def recibir_datos_manos(self, result, output_image, timestamp_ms):
        """Callback del HandLandmarker."""
        if not result.hand_landmarks:
            return
        # TODO: self.hands.procesar(result.hand_landmarks, result.handedness)

    def recibir_transcripcion(self, texto: str, metadata: dict):
        """
        Callback del MotorDeAudio. Actualiza estado y delega a la IA.
        Ya se ejecuta en un hilo daemon separado.
        """
        print(f"\n{'='*60}")
        print(f"🎙️  TRANSCRIPCIÓN: '{texto}'")
        print(f"   Idioma: {metadata.get('idioma', 'N/A')}")
        print(f"{'='*60}\n")

        self.estado["ultimo_texto"] = texto
        self.ia.procesar_texto(texto, metadata)

    # ==========================================================================
    # APLICAR RESULTADO FACIAL (seguimiento de cara en tiempo real)
    # ==========================================================================

    def _aplicar_resultado_facial(self, r: dict):
        """
        Toma el diccionario de ProcesadorFacial y mueve los servos
        de ojos y mandíbula según el seguimiento en tiempo real.
        La IA puede sobreescribir estos valores con sus propias expresiones.
        """
        if r["ojo_desviacion_H"] is not None:
            self.estado["ojo_desviacion_H"] = r["ojo_desviacion_H"]
            self._enviar_ojo_H(r["ojo_desviacion_H"])

        if r["ojo_desviacion_V"] is not None:
            self.estado["ojo_desviacion_V"] = r["ojo_desviacion_V"]
            self._enviar_ojo_V(r["ojo_desviacion_V"])

        if r["boca"] is not None:
            self.estado["boca"] = r["boca"]
            # Solo imitamos la boca del usuario si el robot NO está hablando
            if not self.tts.hablando:
                self._enviar_mandibula(r["boca"])

    def _enviar_ojo_H(self, desviacion: float):
        _RANGO_H = 0.05
        ratio  = (desviacion + _RANGO_H) / (_RANGO_H * 2)
        angulo = int(_clamp01(ratio) * 180)
        try:
            self.gestor.enviar_motor(self.MOTOR_OJO_IZQ_H, angulo)
            self.gestor.enviar_motor(self.MOTOR_OJO_DER_H, angulo)
        except Exception as e:
            print(f"[Callbacks] Error Ojo H: {e}")

    def _enviar_ojo_V(self, desviacion: float):
        _RANGO_V = 0.03
        ratio  = (desviacion + _RANGO_V) / (_RANGO_V * 2)
        angulo = int(_clamp01(ratio) * 180)
        try:
            self.gestor.enviar_motor(self.MOTOR_OJO_IZQ_V, angulo)
            self.gestor.enviar_motor(self.MOTOR_OJO_DER_V, angulo)
        except Exception as e:
            print(f"[Callbacks] Error Ojo V: {e}")

    def _enviar_mandibula(self, score: float):
        angulo = int(score * 45)   # máx 45° según protocolo físico
        self.gestor.enviar_motor(self.MOTOR_MANDIBULA, angulo)

    # ==========================================================================
    # ACCIONES EXTERNAS
    # ==========================================================================

    def resetear_calibracion(self):
        """Recalibra el seguimiento de iris sin reiniciar."""
        self.facial.resetear_calibracion()

    def limpiar_historial_ia(self):
        """Limpia el historial de conversación de la IA."""
        self.ia.limpiar_historial()

    def centrar_todo(self):
        """Centra todos los motores a 90°."""
        self.gestor.centrar_todo()

    def cerrar(self):
        """Libera recursos del TTS y detiene cualquier habla en curso."""
        self.tts.cerrar()


# ── Utilidad ──────────────────────────────────────────────────────────────────

def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))