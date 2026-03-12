import sounddevice as sd
import numpy as np
import threading
import time
from typing import Optional, Callable

class AudioRecorder:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.recording = False
        self.audio_data = []
        self.stream: Optional[sd.InputStream] = None
        
    def start_recording(self):
        """Start recording from microphone"""
        self.recording = True
        self.audio_data = []
        
        def callback(indata, frames, time, status):
            if self.recording:
                self.audio_data.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=callback,
            dtype='int16'
        )
        self.stream.start()
        print("Recording started...")  # Replace with proper logging
        
    def stop_recording(self) -> np.ndarray:
        """Stop recording and return audio data"""
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            
        if not self.audio_data:
            return np.array([], dtype='int16')
            
        # Concatenate all audio chunks
        audio = np.concatenate(self.audio_data, axis=0)
        return audio.flatten()
    
    def save_audio(self, audio: np.ndarray, filename: str = "temp.wav"):
        """Save audio to file (optional)"""
        import wave
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())