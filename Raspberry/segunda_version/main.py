# main.py (INTEGRADO CON AUDIO + IA GROQ)
import cv2
import signal
import sys
import os

from core.vision import MotorDeVision
from core.callbacks import ProcesadorDeCallbacks
from core.audio import MotorDeAudio
from utils.vad import SileroVAD
from services.transcription import ServicioTranscripcion
from services.esp32 import ConexionESP32

from dotenv import load_dotenv
# ==========================================
# CONFIGURACIÓN
# ==========================================

# API key de Groq — preferiblemente vía variable de entorno:
#   export GROQ_API_KEY="gsk_..."
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODELO  ="llama3-8b-8192" #"llama-3.3-70b-versatile"   # o "llama-3.1-8b-instant" para más velocidad

estado_zoe = {
    "modo": "None",
    "boca": "cerrada",
    "ultimo_texto": "",
    "escuchando": True
}

ejecutando = True

# ==========================================
# SEÑAL DE SALIDA
# ==========================================

def manejador_salida(sig, frame):
    global ejecutando
    print("\n\n⏹️ Cerrando...")
    ejecutando = False

signal.signal(signal.SIGINT, manejador_salida)

# ==========================================
# MAIN
# ==========================================

def main():
    global ejecutando

    print("🤖 Iniciando Zoé - Sistema Multimodal con IA")
    print("=" * 60)

    if GROQ_API_KEY == "TU_API_KEY_AQUI":
        print("⚠️  ADVERTENCIA: GROQ_API_KEY no configurada.")
        print("   Usa: export GROQ_API_KEY='gsk_...'\n")

    # 1. ESP32
    print("\n[1/5] Conectando con ESP32...")
    esp = ConexionESP32()
    esp.conectar_automatico()

    # 2. Callbacks + IA
    print("\n[2/5] Inicializando callbacks + GestorExpresiones + IA Groq...")
    procesador = ProcesadorDeCallbacks(
        estado_robot=estado_zoe,
        esp32_serial=esp,
        groq_api_key=GROQ_API_KEY,
        groq_modelo=GROQ_MODELO
    )

    # 3. Visión
    print("\n[3/5] Cargando modelos de visión...")
    motor_vision = MotorDeVision(
        ruta_modelo_cara="Raspberry/segunda_version/tasks/vision/face_landmarker.task",
        ruta_modelo_pose="Raspberry/segunda_version/tasks/vision/pose_landmarker_lite.task",
        ruta_modelo_manos="Raspberry/segunda_version/tasks/vision/hand_landmarker.task",
        callback_cara=procesador.recibir_datos_cara,
        callback_pose=procesador.recibir_datos_pose,
        callback_manos=procesador.recibir_datos_manos
    )

    # 4. Audio
    print("\n[4/5] Inicializando sistema de audio...")
    vad = SileroVAD(threshold=0.5, sample_rate=16000)
    transcriptor = ServicioTranscripcion(modelo_local="medium", idioma="es", groq_api_key=GROQ_API_KEY)
    motor_audio = MotorDeAudio(
        vad_detector=vad,
        transcription_service=transcriptor,
        callback_transcripcion=procesador.recibir_transcripcion,
        sample_rate=16000,
        chunk_size=512,
        silence_duration=1.0,
        min_speech_duration=0.3,
        input_device_index=1
    )

    # 5. Cámara
    print("\n[5/5] Inicializando cámara...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("\n" + "=" * 60)
    print("✅ Todos los sistemas iniciados")
    print("=" * 60)
    print("\n📋 CONTROLES:")
    print("   ESC → Salir")
    print("   M   → Cambiar modo de visión")
    print("   A   → Activar/Desactivar audio")
    print("   H   → Limpiar historial de IA")
    print("   C   → Centrar todos los motores")
    print("   R   → Recalibrar seguimiento de ojos")
    print()

    motor_audio.iniciar()

    # ==========================================
    # BUCLE PRINCIPAL
    # ==========================================

    try:
        while ejecutando and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Sin frame de cámara")
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            motor_vision.procesar_frame(frame_rgb, estado_zoe["modo"])

            # HUD
            cv2.putText(frame, f"Modo: {estado_zoe['modo']}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            color_audio = (0, 255, 0) if estado_zoe["escuchando"] else (0, 0, 255)
            cv2.putText(frame, f"Audio: {'ON' if estado_zoe['escuchando'] else 'OFF'}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_audio, 2)
            if estado_zoe.get("ultimo_texto"):
                cv2.putText(frame, f"'{estado_zoe['ultimo_texto'][:50]}'",
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

            cv2.imshow("Zoe - Vision + Audio + IA", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == 27:   # ESC
                ejecutando = False

            elif key in (ord('m'), ord('M')):
                modos = ["Cara", "Pose", "Manos"]
                idx = modos.index(estado_zoe["modo"]) if estado_zoe["modo"] in modos else -1
                estado_zoe["modo"] = modos[(idx + 1) % len(modos)]
                print(f"🔄 Modo: {estado_zoe['modo']}")

            elif key in (ord('a'), ord('A')):
                estado_zoe["escuchando"] = not estado_zoe["escuchando"]
                if estado_zoe["escuchando"]:
                    motor_audio.iniciar()
                    print("🎤 Audio ON")
                else:
                    motor_audio.detener()
                    print("🔇 Audio OFF")

            elif key in (ord('h'), ord('H')):
                procesador.limpiar_historial_ia()

            elif key in (ord('c'), ord('C')):
                procesador.centrar_todo()
                print("⚙️ Motores centrados")

            elif key in (ord('r'), ord('R')):
                procesador.resetear_calibracion()
                print("🔄 Recalibrando ojos...")

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🧹 Cerrando...")
        procesador.cerrar()        # TTS + detener habla
        motor_audio.cerrar()
        motor_vision.cerrar_modelos()
        cap.release()
        cv2.destroyAllWindows()
        if esp:
            esp.desconectar()
        print("✅ ¡Hasta luego! 👋\n")


if __name__ == "__main__":
    main()