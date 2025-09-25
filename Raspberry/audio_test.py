import mediapipe as mp
import pyaudio
import numpy as np
import wave
import time

# --- Configuración de Parámetros ---

# Parámetros del flujo de audio
CHUNK = 1024  # Tamaño del fragmento de audio a procesar a la vez
FORMAT = pyaudio.paInt16  # Formato de 16 bits
CHANNELS = 1  # Audio mono
RATE = 16000  # Frecuencia de muestreo (Hz), óptima para Yamnet

# Parámetros de detección y grabación
# El umbral de confianza para la etiqueta 'Speech'
SPEECH_THRESHOLD = 0.5  
# Duración de silencio para detener la grabación (en segundos)
SILENCE_DURATION = 2  

# --- Inicialización de MediaPipe y PyAudio ---

# Carga el modelo Yamnet
BaseOptions = mp.tasks.BaseOptions
AudioClassifier = mp.tasks.audio.AudioClassifier
AudioClassifierOptions = mp.tasks.audio.AudioClassifierOptions
RunningMode = mp.tasks.audio.RunningMode
is_recording = False
frames = []
last_speech_time = time.time()
def mi_callback(result, audio_data, timestamp_ms: int):
    print("Callback invocado")
    global is_recording, frames, last_speech_time

    # Busca la etiqueta 'Speech'
    speech_detected = False
    if result.classifications:
        for category in result.classifications[0].categories:
            if 'Speech' in category.category_name and category.score > SPEECH_THRESHOLD:
                speech_detected = True
                last_speech_time = time.time()
                break

    # --- Lógica de grabación ---
    if speech_detected and not is_recording:
        print("¡Voz detectada! Empezando a grabar...")
        is_recording = True
        frames = []

    if is_recording:
        frames.append(audio_data.audio_buffer)  # Guarda el fragmento
        if time.time() - last_speech_time > SILENCE_DURATION:
            is_recording = False
            if frames:
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                output_filename = f"grabacion_voz_{timestamp}.wav"
                wf = wave.open(output_filename, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()
                print(f"Grabación guardada como '{output_filename}'")
            frames = []
            print("Esperando a que empiece a hablar de nuevo...")
# La ruta a tu archivo Yamnet
model_path = 'models/yamnet.tflite'
options = AudioClassifierOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    max_results=3,,
    running_mode=RunningMode.AUDIO_STREAM,
    result_callback= mi_callback,  # <-- Aquí agregas el callback
)

# Crea el clasificador de audio
with AudioClassifier.create_from_options(options) as classifier:
    # Inicia el objeto PyAudio
    p = pyaudio.PyAudio()

    # Abre el flujo de audio del micrófono
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print("¡Escuchando! Esperando a que empiece a hablar...")

    # --- Bucle Principal de Detección y Grabación ---

    is_recording = False
    frames = []
    last_speech_time = time.time()

    try:
        timestamp_ms = int(time.time() * 1000)
        samples_processed = 0
        while True:
            print("bucle...")
            data = stream.read(CHUNK)
            audio_data_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            audio_data_mp = mp.tasks.components.containers.AudioData.create_from_array(audio_data_np, RATE)
            classifier.classify_async(audio_data_mp, timestamp_ms)
            # Avanza el timestamp según los samples procesados
            samples_processed += CHUNK
            timestamp_ms += int((CHUNK / RATE) * 1000)
    except ValueError as e:
        print(f"Error de valor: {e}")

    except KeyboardInterrupt:
        # Maneja la interrupción del usuario (Ctrl+C)
        print("\nPrograma terminado por el usuario.")
    
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        

    finally:
        # Cierra los recursos de audio de forma segura
        stream.stop_stream()
        stream.close()
        p.terminate()