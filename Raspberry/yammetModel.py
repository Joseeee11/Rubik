import mediapipe as mp
import numpy as np
import time
import pyaudio
import json
import threading

mp_tasks = mp.tasks
AudioClassifier = mp_tasks.audio.AudioClassifier
AudioClassifierOptions = mp_tasks.audio.AudioClassifierOptions
AudioClassifierResult = mp_tasks.audio.AudioClassifierResult
AudioRunningMode = mp_tasks.audio.RunningMode
BaseOptions = mp_tasks.BaseOptions


class YammetModel:

    def print_result(self, result: AudioClassifierResult, timestamp_ms: int):
        if timestamp_ms is None:
            timestamp_ms = self.timestamp_ms

        try:
            # Construir salida ordenada
            lines = []
            lines.append(f"AudioClassifierResult at {self.timestamp_ms} ms y reales :{timestamp_ms}:")
            for i, classifications in enumerate(result.classifications):
                lines.append(f"  Head {i} ({classifications.head_name}):")
                # ordenar categorías por score descendente
                cats = sorted(classifications.categories, key=lambda c: c.score, reverse=True)
                for c in cats:
                    name = c.category_name or "(sin_nombre)"
                    lines.append(f"    - {name:30s} score={c.score:.3f} (idx={c.index})")
                    # detectar 'Speech'
                    if name.lower() == "speech" and c.score >= self.speech_threshold:
                        # actualizar estado de grabación 
                        self.last_speech_time = time.time()
                        if not self.is_recording:
                            # si no se estaba grabando pasa a grabar, si ya se estaba grabando no se entra aquí 
                            self.is_recording = True
                            print("[Voz detectada] empezando grabación")
                # si ninguna categoría superó el umbral, comprobar silencio por timeout
            # comprobar timeout de silencio para cambiar is_recording a False
            if self.is_recording and (time.time() - self.last_speech_time) > self.silence_timeout:
                self.is_recording = False
                print("[Silencio] deteniendo grabación")

            # imprimir resultado formateado
            print("\n".join(lines))
        except Exception as e:
            print('Error printing result: {}'.format(e))

    def __init__(self):
        base_options = BaseOptions(model_asset_path='./models/yamnet.tflite')
        running_mode=AudioRunningMode.AUDIO_STREAM
        max_results=3

        # estado de grabación / umbrales
        self.is_recording = False
        self.speech_threshold = 0.30   # configurable: score mínimo para considerar "speech"
        self.silence_timeout = 2.0     # segundos sin speech para considerar que terminó
        self.last_speech_time = 0.0

    

        self.options= AudioClassifierOptions(
            base_options=base_options,
            running_mode=running_mode,
            max_results=max_results,
            result_callback=self.print_result
        )
        self.actualizarTimestamp()

        self.classifier = None
        self.classifier_lock = threading.Lock()
        try:
            # crear el classifier una sola vez
            self.classifier = AudioClassifier.create_from_options(self.options)
        except Exception as e:
            print("No se pudo crear el classifier en __init__:", e)
            self.classifier = None

    def actualizarTimestamp(self):
        self.timestamp_ms = time.time_ns() // 1_000_000

    def streamingClassification(self, audio_streaming, timestamp_ms:int):
        if timestamp_ms is None:
            timestamp_ms = time.time_ns() // 1_000_000
            self.actualizarTimestamp()
        else:
            self.timestamp_ms = timestamp_ms

        if self.classifier is None:
            raise RuntimeError("classifier no inicializado")
        # preparar audio
        audio_data = np.frombuffer(audio_streaming, dtype=np.int16)
        audio_data_mp = self.normalize_audio(audio_data)
        # proteger acceso si hay hilos
        with self.classifier_lock:
            self.classifier.classify_async(audio_data_mp, timestamp_ms)


    def normalize_audio(self, audio_data, sample_rate=16000):
        audio_data_np = audio_data.astype('float32') / np.iinfo(np.int16).max
        audio_data_mp = mp.tasks.components.containers.AudioData.create_from_array(
            audio_data_np, sample_rate)
        return audio_data_mp
    
    def close(self):
        """Cerrar el classifier de forma segura."""
        if getattr(self, "classifier", None) is None:
            return
        try:
            # Si el objeto ofrece close()
            if hasattr(self.classifier, "close"):
                self.classifier.close()
            # Si fue creado como context manager, intentar __exit__
            elif hasattr(self.classifier, "__exit__"):
                self.classifier.__exit__(None, None, None)
        except Exception as e:
            print("Error cerrando classifier:", e)
        finally:
            self.classifier = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        # fallback por si olvidas llamar close()
        try:
            self.close()
        except Exception:
            pass








######## Prueba del modelo #################################################
if __name__ == "__main__":
    yammet = YammetModel()
    # Aquí se debería agregar el código para obtener un flujo de audio y pasarlo a streamingClassification
    # Por ejemplo:
    # Audio stream parameters
    FORMAT = pyaudio.paInt16  # Corresponds to 16-bit audio
    CHANNELS = 1 # Mono audio
    RATE = 16000  # Sample rate (Hz) - Needs to match MediaPipe's expected rate
    CHUNK = 1024  # Number of frames per buffer
    audio_instance = pyaudio.PyAudio()
    
    # listar dispositivos (útil para depuración)
    print("Dispositivos de audio disponibles:")
    for i in range(audio_instance.get_device_count()):
        info = audio_instance.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0:
            print(f"  idx={i} name='{info.get('name')}' channels={info.get('maxInputChannels')}")
    # elige el dispositivo por defecto si no quieres fijar uno
    try:
        default_info = audio_instance.get_default_input_device_info()
        dev_index = default_info['index']
        mic_name = default_info.get('name', f"device_{dev_index}")
    except Exception:
        dev_index = None
        mic_name = "desconocido"
        
    print(f"Iniciando captura de audio. Mic seleccionado: {mic_name} (index={dev_index})")

    stream = audio_instance.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)
    print("Iniciando la captura de audio...")
    # preparar timestamp coherente
    timestamp_ms = int(time.time() * 1000)
    chunk_ms = int((CHUNK / RATE) * 1000)  # ms por fragmento

    try:
        with yammet if hasattr(yammet, "__enter__") else nullcontext():
            while True:
                audio_streaming = stream.read(CHUNK, exception_on_overflow=False)

                yammet.streamingClassification(audio_streaming= audio_streaming, timestamp_ms = timestamp_ms)
                print(timestamp_ms)
                timestamp_ms += chunk_ms
    except KeyboardInterrupt:
        print("Captura de audio detenida.")

    except Exception as e:
            print('Error bucle: {}'.format(e))
    finally:
        ## 9223372036854775
        ## 9223372036854775
        ## 9223372036854775
    
        yammet.close()
        # cerrar stream y mostrar resumen
        try:
            stream.stop_stream()
            stream.close()
            audio_instance.terminate()
        except Exception as e:
            print('Error al parar: ', e)
        try:
            dev_index = stream._input_device_index
            dev_info = audio_instance.get_device_info_by_index(dev_index)
            mic_name = dev_info.get("name", f"device_{dev_index}")
            
            print(f"Micrófono usado2: {mic_name}")
        except Exception:
            mic_name = "desconocido"

    print(f"Micrófono usado: {mic_name}")