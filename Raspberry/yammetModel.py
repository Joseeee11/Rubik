import mediapipe as mp
import numpy as np
import time
import pyaudio
import json
from collections import deque
import threading
from contextlib import nullcontext
import wave
import io
from pathlib import Path
import os
import shutil
import tempfile
import site

mp_tasks = mp.tasks
AudioClassifier = mp_tasks.audio.AudioClassifier
AudioClassifierOptions = mp_tasks.audio.AudioClassifierOptions
AudioClassifierResult = mp_tasks.audio.AudioClassifierResult
AudioRunningMode = mp_tasks.audio.RunningMode
BaseOptions = mp_tasks.BaseOptions


class YammetModel:

    def print_result(self, result, timestamp_ms: int):
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
                            print("[Voz detectada] empezando grabación")
                            with self.record_lock:
                                while self.prebuffer:
                                    self.recording_frames.append(self.prebuffer.popleft())
                                self.is_recording = True

                # si ninguna categoría superó el umbral, comprobar silencio por timeout
            # comprobar timeout de silencio para cambiar is_recording a False
            if self.is_recording and (time.time() - self.last_speech_time) > self.silence_timeout:
                self.is_recording = False
                print("[Silencio] deteniendo grabación")
                with self.record_lock:
                    if self.recording_frames:
                        frame_copia= self.recording_frames[:]
                        self.recording_frames= []
                        wav_copia= self._frames_to_wav_bytes(frame_copia)
                        self.grabacionDeVoz=wav_copia
                        print("guardar grabado")
                        # self.guardar_grabacion(f'grabacion{self.last_speech_time}.wav')
            # imprimir resultado formateado
            print("\n".join(lines))
        except Exception as e:
            print('Error printing result: {}'.format(e))

    def __init__(self,model_path:str = None, model_buffer = None):
        
        if model_buffer is not None:
            base_options = BaseOptions(model_asset_buffer=model_buffer)
            running_mode=AudioRunningMode.AUDIO_STREAM
            max_results=3
            
            self.options= AudioClassifierOptions(
                base_options=base_options,
                running_mode=running_mode,
                max_results=max_results,
                result_callback=self.print_result
            )
            
            # Yamnet inicio: intentar crear el classifier con tolerancia a rutas en Windows
            self.classifier = None
            self.classifier_lock = threading.Lock()
            try:
                
                self.classifier = AudioClassifier.create_from_options(self.options)
            except Exception as buffError:
                print("errror en errorbuffer: ", buffError)

        # determinar ruta del modelo relativa al archivo
        elif model_path is None:
            model_path = Path(__file__).resolve().parent / "models" / "yamnet.tflite"
            # Convierte a formato POSIX para máxima compatibilidad con librerías nativas
            model_path_str = model_path.as_posix()
            if not model_path.exists():
                self.classifier = None
                print('ruta no encontrada: ',model_path)
                self._last_creation_error = FileNotFoundError(f"Modelo no encontrado: {str(model_path)}")
                print(self._last_creation_error)
            else: 
                
                print('ruta: ',model_path_str)
                base_options = BaseOptions(model_asset_path=str(model_path_str))
                
                print('ruta baseoptions: ',base_options)
                running_mode=AudioRunningMode.AUDIO_STREAM
                max_results=3
                
                self.options= AudioClassifierOptions(
                    base_options=base_options,
                    running_mode=running_mode,
                    max_results=max_results,
                    result_callback=self.print_result
                )
                
                # Yamnet inicio: intentar crear el classifier con tolerancia a rutas en Windows
                self.classifier = None
                self.classifier_lock = threading.Lock()
                try:
                    # crear el classifier una sola vez (intento directo)
                    self.classifier = AudioClassifier.create_from_options(self.options)
                except Exception as e:
                    # Si falla, intentar varias estrategias (Paths con slash, file://, y copia temporal)
                    print("No se pudo crear el classifier en __init__:", repr(e))
                    p = Path(model_path)
                    alt_tried = []
                    # construir lista de rutas alternativas
                    try_paths = []
                    try_paths.append(str(p))
                    try_paths.append(p.as_posix())
                    # file URI
                    try_paths.append("file://" + p.as_posix())
                    # UNC style (\?\C:\...)
                    try:
                        try_paths.append(r"\\?\\" + str(p))
                    except Exception:
                        pass

                    for tp in try_paths:
                        try:
                            print("Intentando crear classifier con model_asset_path:", tp)
                            alt_opts = AudioClassifierOptions(
                                base_options=BaseOptions(model_asset_path=str(tp)),
                                running_mode=running_mode,
                                max_results=max_results,
                                result_callback=self.print_result,
                            )
                            self.classifier = AudioClassifier.create_from_options(alt_opts)
                            self.options = alt_opts
                            print("Classifier creado usando ruta alternativa:", tp)
                            break
                        except Exception as e2:
                            alt_tried.append((tp, repr(e2)))
                            print("Fallo con ruta alternativa:", tp, repr(e2))

                    # Si aún no se creó, intentar copiar el archivo del modelo a un directorio temporal
                    if self.classifier is None:
                        try:
                            tempdir = tempfile.mkdtemp(prefix="yamnet_model_")
                            dest = Path(tempdir) / "yamnet.tflite"
                            shutil.copyfile(str(p), str(dest))
                            tp = str(dest)
                            print("Intentando crear classifier con copia temporal:", tp)
                            temp_opts = AudioClassifierOptions(
                                base_options=BaseOptions(model_asset_path=tp),
                                running_mode=running_mode,
                                max_results=max_results,
                                result_callback=self.print_result,
                            )
                            self.classifier = AudioClassifier.create_from_options(temp_opts)
                            self.options = temp_opts
                            print("Classifier creado usando copia temporal:", tp)
                        except Exception as e3:
                            self.classifier = None
                            self._last_creation_error = e3
                            print("No se pudo crear el classifier con ninguna estrategia:", repr(e3))
                        # Intentar copiar el modelo dentro de site-packages y usar solo el basename
                        if self.classifier is None:
                            try:
                                site_pkgs = []
                                try:
                                    site_pkgs = site.getsitepackages()
                                except Exception:
                                    try:
                                        site_pkgs = [site.getusersitepackages()]
                                    except Exception:
                                        site_pkgs = []
                                for sp in site_pkgs:
                                    try:
                                        sp_path = Path(sp)
                                        if not sp_path.exists():
                                            continue
                                        # crear un nombre único en site-packages
                                        dest_sp = sp_path / f"yamnet_mediapipe_{int(time.time())}.tflite"
                                        shutil.copyfile(str(p), str(dest_sp))
                                        print("Intentando crear classifier usando archivo en site-packages:", dest_sp)
                                        sp_opts = AudioClassifierOptions(
                                            base_options=BaseOptions(model_asset_path=dest_sp.name),
                                            running_mode=running_mode,
                                            max_results=max_results,
                                            result_callback=self.print_result,
                                        )
                                        self.classifier = AudioClassifier.create_from_options(sp_opts)
                                        self.options = sp_opts
                                        # marcar para eliminar luego
                                        self._sitepkg_model_path = dest_sp
                                        print("Classifier creado usando archivo en site-packages:", dest_sp)
                                        break
                                    except Exception as e4:
                                        print("Fallo al intentar en site-packages:", sp, repr(e4))
                                if self.classifier is None:
                                    print("No se pudo crear classifier desde site-packages.")
                            except Exception as e5:
                                print("Error intentando usar site-packages:", repr(e5))
        else: 
            print('ruta: ',model_path)
            base_options = BaseOptions(model_asset_path=str(model_path))
            running_mode=AudioRunningMode.AUDIO_STREAM
            max_results=3
            
            self.options= AudioClassifierOptions(
                base_options=base_options,
                running_mode=running_mode,
                max_results=max_results,
                result_callback=self.print_result
            )
            
            # Yamnet inicio: intentar crear el classifier con tolerancia a rutas en Windows
            self.classifier = None
            self.classifier_lock = threading.Lock()
            try:
                # crear el classifier una sola vez (intento directo)
                self.classifier = AudioClassifier.create_from_options(self.options)
            except Exception as e:
                print("No se pudo crear el classifier en __init__:", repr(e))
                p = Path(model_path)
                alt_tried = []
                try_paths = [str(p), p.as_posix(), "file://" + p.as_posix()]
                try:
                    try_paths.append(r"\\?\\" + str(p))
                except Exception:
                    pass

                for tp in try_paths:
                    try:
                        print("Intentando crear classifier con model_asset_path:", tp)
                        alt_opts = AudioClassifierOptions(
                            base_options=BaseOptions(model_asset_path=str(tp)),
                            running_mode=running_mode,
                            max_results=max_results,
                            result_callback=self.print_result,
                        )
                        self.classifier = AudioClassifier.create_from_options(alt_opts)
                        self.options = alt_opts
                        print("Classifier creado usando ruta alternativa:", tp)
                        break
                    except Exception as e2:
                        alt_tried.append((tp, repr(e2)))
                        print("Fallo con ruta alternativa:", tp, repr(e2))

                if self.classifier is None:
                    try:
                        tempdir = tempfile.mkdtemp(prefix="yamnet_model_")
                        dest = Path(tempdir) / "yamnet.tflite"
                        shutil.copyfile(str(p), str(dest))
                        tp = str(dest)
                        print("Intentando crear classifier con copia temporal:", tp)
                        temp_opts = AudioClassifierOptions(
                            base_options=BaseOptions(model_asset_path=tp),
                            running_mode=running_mode,
                            max_results=max_results,
                            result_callback=self.print_result,
                        )
                        self.classifier = AudioClassifier.create_from_options(temp_opts)
                        self.options = temp_opts
                        print("Classifier creado usando copia temporal:", tp)
                    except Exception as e3:
                        self.classifier = None
                        self._last_creation_error = e3
                        print("No se pudo crear el classifier con ninguna estrategia:", repr(e3))
        # estado de grabación / umbrales
        self.is_recording = False
        self.speech_threshold = 0.80   # configurable: score mínimo para considerar "speech"
        self.silence_timeout = 1.5     # segundos sin speech para considerar que terminó
        self.last_speech_time = 0.0
        self.grabacionDeVoz = None
        # buffers para grabación por voz (pre-roll)
        self.pre_roll_chunks = 24
        self.prebuffer = deque(maxlen=self.pre_roll_chunks)
        self.recording_frames = []
        self.record_lock = threading.Lock()
        # PyAudio
        self.sample_rate= 16000
        self.channels=1
        self.sample_width_bytes=2 # 2bytes = 16bits

        self.actualizarTimestamp()

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
        if not hasattr(self, 'classifier_lock'):
            print("ADVERTENCIA: classifier_lock no existe, recreando...")
            self.classifier_lock = threading.Lock()

        # preparar audio
        audio_data = np.frombuffer(audio_streaming, dtype=np.int16)
        audio_data_mp = self.normalize_audio(audio_data)
        # proteger acceso si hay hilos
        with self.classifier_lock:
            self.prebuffer.append(audio_streaming)
            if self.is_recording:
                self.recording_frames.append(audio_streaming)
            self.classifier.classify_async(audio_data_mp, timestamp_ms)


    def normalize_audio(self, audio_data, sample_rate=16000):
        audio_data_np = audio_data.astype('float32') / np.iinfo(np.int16).max
        audio_data_mp = mp.tasks.components.containers.AudioData.create_from_array(
            audio_data_np, sample_rate)
        return audio_data_mp
    
    def guardar_grabacion(self, filename="grabacion.wav"):
        """
        Guarda el contenido de self.grabacionDeVoz en un archivo WAV.
        """
        if self.grabacionDeVoz is not None:
            try:
                with open(filename, "wb") as wav_file:
                    wav_file.write(self.grabacionDeVoz)
                print(f"Grabación guardada como: {filename}")
            except Exception as e:
                print(f"Error al guardar la grabación: {e}")
        else:
            print("No hay grabación para guardar.")

    
    # ---------- Conversión frames -> WAV bytes ----------
    def _frames_to_wav_bytes(self, frames_list):
        """
        Recibe lista de chunks (bytes PCM int16) y devuelve bytes con encabezado WAV.
        """
        try:
            bio = io.BytesIO()
            with wave.open(bio, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.sample_width_bytes)
                wf.setframerate(self.sample_rate)
                wf.writeframes(b"".join(frames_list))
            return bio.getvalue()
        except Exception as e:
            print("Error generando WAV en memoria:", e)
            return None
    
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
            # limpiar archivo temporal colocado en site-packages si existe
            try:
                if getattr(self, "_sitepkg_model_path", None) is not None:
                    try:
                        spath = Path(self._sitepkg_model_path)
                        if spath.exists():
                            spath.unlink()
                            print("Eliminado modelo temporal de site-packages:", spath)
                    except Exception as ex:
                        print("No se pudo eliminar el archivo temporal en site-packages:", ex)
                    self._sitepkg_model_path = None
            except Exception:
                pass

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
                if yammet.grabacionDeVoz is not None:
                    print("en teroria se grabó")
                    yammet.grabacionDeVoz = None
                # print(timestamp_ms)
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