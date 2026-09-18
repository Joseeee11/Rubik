# core/audio.py
import pyaudio
import numpy as np
import threading
import queue
import time
from typing import Callable, Optional
from collections import deque

class MotorDeAudio:
    """
    Motor de captura y procesamiento de audio en tiempo real.
    Ejecuta en un hilo separado para no bloquear el hilo principal.
    """
    
    def __init__(self,
                 vad_detector,
                 transcription_service,
                 callback_transcripcion: Optional[Callable] = None,
                 sample_rate: int = 16000,
                 chunk_size: int = 512,
                 channels: int = 1,
                 silence_duration: float = 1.0,
                 min_speech_duration: float = 0.3,
                 input_device_index: int = None):
        """
        Args:
            vad_detector: Instancia de SileroVAD
            transcription_service: Instancia de ServicioTranscripcion
            callback_transcripcion: Función a llamar cuando se complete una transcripción
            sample_rate: Frecuencia de muestreo (16000 Hz recomendado)
            chunk_size: Tamaño de cada chunk de audio en samples
            channels: Número de canales (1 = mono, 2 = estéreo)
            silence_duration: Segundos de silencio para considerar fin de frase
            min_speech_duration: Duración mínima de voz para transcribir
        """
        self.vad = vad_detector
        self.transcriptor = transcription_service
        self.callback_transcripcion = callback_transcripcion
        
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.silence_duration = silence_duration
        self.min_speech_duration = min_speech_duration
        self.input_device_index = input_device_index
        
        # PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Control de hilos
        self.hilo_captura = None
        self.hilo_procesamiento = None
        self.ejecutando = False
        
        # Colas para comunicación entre hilos
        self.cola_audio = queue.Queue(maxsize=500)
        self.cola_transcripcion = queue.Queue(maxsize=10)
        
        # Buffer para acumular audio de voz
        self.buffer_voz = deque(maxlen=int(sample_rate * 30))  # Máx 30 segundos
        self.frames_silencio = 0
        self.frames_voz = 0
        self.max_frames_silencio = int((silence_duration * sample_rate) / chunk_size)
        self.min_frames_voz = int((min_speech_duration * sample_rate) / chunk_size)
        self.capturando_voz = False
        
        print(f"🎤 Motor de Audio inicializado:")
        print(f"   - Sample Rate: {sample_rate} Hz")
        print(f"   - Chunk Size: {chunk_size} samples")
        print(f"   - Silencio para corte: {silence_duration}s")
        print(f"   - Mínimo de voz: {min_speech_duration}s")
    
    def _captura_audio(self):
        """Hilo de captura de audio desde el micrófono."""
        print("🎙️ Hilo de captura de audio iniciado")
        
        while self.ejecutando:
            try:
                # Leer chunk de audio
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Convertir a numpy array
                audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                audio_chunk = audio_chunk / 32768.0  # Normalizar a [-1.0, 1.0]
                
                # Enviar a cola de procesamiento
                if not self.cola_audio.full():
                    self.cola_audio.put(audio_chunk)
                else:
                    print("⚠️ Cola de audio llena, descartando chunk")
                    
            except Exception as e:
                if self.ejecutando:  # Solo mostrar error si no estamos cerrando
                    print(f"❌ Error en captura de audio: {e}")
                break
        
        print("🛑 Hilo de captura de audio finalizado")
    
    def _procesa_audio(self):
        """Hilo de procesamiento VAD y transcripción."""
        print("🔊 Hilo de procesamiento de audio iniciado")
        
        while self.ejecutando:
            try:
                # Obtener chunk de la cola (timeout para permitir salida limpia)
                try:
                    audio_chunk = self.cola_audio.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Detectar voz con VAD
                hay_voz = self.vad.is_speech(audio_chunk)
                probabilidad = self.vad.get_speech_probability(audio_chunk)
                
                if hay_voz:
                    # Hay voz: acumular en buffer
                    self.buffer_voz.extend(audio_chunk)
                    self.frames_voz += 1
                    self.frames_silencio = 0
                    
                    if not self.capturando_voz:
                        self.capturando_voz = True
                        print(f"🗣️ Voz detectada (p={probabilidad:.2f})")
                else:
                    # No hay voz
                    if self.capturando_voz:
                        # Estábamos capturando voz, contar silencio
                        self.frames_silencio += 1
                        
                        # Seguir añadiendo al buffer (para capturar el final)
                        self.buffer_voz.extend(audio_chunk)
                        
                        # Si hay suficiente silencio, procesar la captura
                        if self.frames_silencio >= self.max_frames_silencio:
                            if self.frames_voz >= self.min_frames_voz:
                                print(f"✂️ Fin de frase detectado ({self.frames_voz} frames de voz)")
                                self._procesar_captura()
                            else:
                                print(f"⏭️ Voz muy corta, descartando ({self.frames_voz} frames)")
                            
                            # Resetear estado
                            self._resetear_captura()
                
            except Exception as e:
                print(f"❌ Error en procesamiento de audio: {e}")
                import traceback
                traceback.print_exc()
        
        print("🛑 Hilo de procesamiento de audio finalizado")
    
    def _procesar_captura(self):
        """Procesa el audio capturado y lo transcribe en un hilo separado para no bloquear."""
        try:
            # 1. Hacemos una copia local del audio para que el VAD pueda seguir trabajando
            audio_completo = np.array(self.buffer_voz, dtype=np.float32)
            
            duracion = len(audio_completo) / self.sample_rate
            print(f"📝 Transcribiendo {duracion:.2f}s de audio en segundo plano...")
            
            # 2. Creamos una mini-función que hará el trabajo pesado sin interrumpir
            def tarea_transcripcion(audio_data):
                inicio = time.time()
                resultado = self.transcriptor.transcribir(audio_data, self.sample_rate)
                tiempo_trans = time.time() - inicio
                
                texto = resultado.get("texto", "")
                
                if texto:
                    print(f"✅ Transcripción ({tiempo_trans:.2f}s): {texto}")
                    # Llamar callback si existe
                    if self.callback_transcripcion:
                        self.callback_transcripcion(texto, resultado)
                else:
                    print(f"⚠️ Transcripción vacía")

            # 3. Lanzamos esta tarea en un nuevo hilo independiente
            hilo_transcripcion = threading.Thread(
                target=tarea_transcripcion, 
                args=(audio_completo,), 
                daemon=True
            )
            hilo_transcripcion.start()
            
        except Exception as e:
            print(f"❌ Error al procesar captura: {e}")
            import traceback
            traceback.print_exc()
    
    def _resetear_captura(self):
        """Resetea el estado de captura de voz."""
        self.buffer_voz.clear()
        self.frames_silencio = 0
        self.frames_voz = 0
        self.capturando_voz = False
    
    def iniciar(self):
        """Inicia la captura y procesamiento de audio."""
        if self.ejecutando:
            print("⚠️ Motor de audio ya está ejecutando")
            return
        
        print("▶️ Iniciando motor de audio...")
        
        # Abrir stream de audio
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.input_device_index,
            frames_per_buffer=self.chunk_size
        )
        
        self.ejecutando = True
        
        # Iniciar hilos
        self.hilo_captura = threading.Thread(target=self._captura_audio, daemon=True)
        self.hilo_procesamiento = threading.Thread(target=self._procesa_audio, daemon=True)
        
        self.hilo_captura.start()
        self.hilo_procesamiento.start()
        
        print("✅ Motor de audio en ejecución")
    
    def detener(self):
        """Detiene la captura y procesamiento de audio."""
        if not self.ejecutando:
            return
        
        print("⏹️ Deteniendo motor de audio...")
        self.ejecutando = False
        
        # Esperar a que los hilos terminen
        if self.hilo_captura:
            self.hilo_captura.join(timeout=2.0)
        if self.hilo_procesamiento:
            self.hilo_procesamiento.join(timeout=2.0)
        
        # Cerrar stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        print("✅ Motor de audio detenido")
    
    def cerrar(self):
        """Cierra completamente el motor de audio."""
        self.detener()
        
        if self.audio:
            self.audio.terminate()
        
        print("✅ Motor de audio cerrado")
