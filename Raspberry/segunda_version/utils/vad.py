# utils/vad.py
import torch
import numpy as np
from typing import Callable, Optional
import threading
import queue

class SileroVAD:
    """
    Wrapper para Silero VAD (Voice Activity Detection).
    Detecta cuándo hay voz en el audio de forma eficiente.
    """
    
    def __init__(self, 
                 threshold: float = 0.5,
                 sample_rate: int = 16000,
                 chunk_size: int = 512):
        """
        Args:
            threshold: Umbral de confianza para detectar voz (0.0 - 1.0)
            sample_rate: Frecuencia de muestreo (debe ser 16000 para Silero)
            chunk_size: Tamaño de cada chunk de audio en samples
        """
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        
        # Cargar modelo Silero VAD
        print("🎤 Cargando modelo Silero VAD...")
        self.model, self.utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        
        (self.get_speech_timestamps,
         self.save_audio,
         self.read_audio,
         self.VADIterator,
         self.collect_chunks) = self.utils
        
        # Estado interno
        self._reset_states()
        print("✅ Silero VAD cargado correctamente")
    
    def _reset_states(self):
        """Resetea el estado interno del modelo."""
        self.model.reset_states()
    
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Detecta si hay voz en un chunk de audio.
        
        Args:
            audio_chunk: Array numpy con samples de audio (float32, -1.0 a 1.0)
            
        Returns:
            True si se detecta voz, False si no
        """
        # Convertir a tensor
        audio_tensor = torch.from_numpy(audio_chunk)
        
        # Obtener probabilidad de voz
        speech_prob = self.model(audio_tensor, self.sample_rate).item()
        
        return speech_prob >= self.threshold
    
    def get_speech_probability(self, audio_chunk: np.ndarray) -> float:
        """
        Obtiene la probabilidad de que haya voz en el chunk.
        
        Returns:
            Probabilidad entre 0.0 y 1.0
        """
        audio_tensor = torch.from_numpy(audio_chunk)
        return self.model(audio_tensor, self.sample_rate).item()
