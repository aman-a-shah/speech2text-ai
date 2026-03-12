from faster_whisper import WhisperModel
import numpy as np
import os
from typing import Optional

class Transcriber:
    def __init__(self, model_size: str = "tiny", device: str = "cpu"):
        """
        Initialize Whisper model
        model_size: tiny, base, small, medium, large
        device: cpu, cuda, auto
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        
    def load_model(self):
        """Load the Whisper model (downloaded on first use)"""
        print(f"Loading {self.model_size} model on {self.device}...")
        
        # Model will be downloaded to ~/.cache/huggingface/hub/ [citation:3]
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type="int8"  # Use int8 for CPU, float16 for GPU
        )
        print("Model loaded!")
        
    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text"""
        if self.model is None:
            self.load_model()
            
        # Convert to float32 and normalize
        audio_float = audio.astype(np.float32) / 32768.0
        
        # Transcribe
        segments, info = self.model.transcribe(
            audio_float,
            beam_size=5,  # Higher = more accurate but slower [citation:3]
            language="en",  # Set to None for auto-detect
            vad_filter=True,  # Voice Activity Detection
            vad_parameters=dict(
                threshold=0.7,
                min_speech_duration_ms=100,
                min_silence_duration_ms=500
            )
        )
        
        # Combine all segments
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    
    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe from audio file"""
        if self.model is None:
            self.load_model()
            
        segments, _ = self.model.transcribe(audio_path)
        text = " ".join([segment.text for segment in segments])
        return text.strip()