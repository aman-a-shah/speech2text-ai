#!/usr/bin/env python3
"""
Speech2Text Pro - With Proper Locking (No Infinite Loops)
"""

# === INSTANCE LOCKING - MUST BE FIRST ===
import os
import sys
import fcntl
import tempfile
from pathlib import Path
import time

# Create a lock file to prevent multiple instances
lock_file = Path(tempfile.gettempdir()) / "speech2text.lock"
try:
    # Try to acquire lock
    file_handle = open(lock_file, 'w')
    fcntl.lockf(file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    # Store handle to keep lock alive
    LOCK_FILE_HANDLE = file_handle
    LOCK_FILE_HANDLE.write(str(os.getpid()))
    LOCK_FILE_HANDLE.flush()
except (IOError, OSError):
    # Lock already held - another instance is running
    try:
        with open(lock_file, 'r') as f:
            pid = f.read().strip()
        print(f"Speech2Text is already running (PID: {pid})")
        
        # Show notification
        os.system(f'osascript -e \'display notification "App is already running" with title "Speech2Text"\'')
        
        # Try to bring existing instance to front
        os.system(f'osascript -e \'tell application "System Events" to tell process "Speech2Text Pro" to set frontmost to true\'')
        
        sys.exit(0)
    except:
        sys.exit(0)

# === REST OF IMPORTS ===
import rumps
import sounddevice as sd
import numpy as np
import threading
import queue
import logging
import tempfile
from pathlib import Path
import time
import pyperclip
import subprocess
from pynput import keyboard

# Setup logging
log_dir = Path.home() / ".local" / "share" / "speech2text" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_dir / "app.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add cleanup for lock file on exit
def cleanup_lock():
    try:
        LOCK_FILE_HANDLE.close()
        lock_file.unlink()
    except:
        pass

class Speech2TextApp(rumps.App):
    def __init__(self):
        super(Speech2TextApp, self).__init__("🎤", title="Speech2Text")
        self.menu = [
            "Start Recording",
            "Stop Recording",
            None,
            "Status: Starting up...",
            None,
            "Auto-Paste: ON",
            "Model: tiny",
            None,
            "Keybinds: ⌘⇧Space",
            None,
            "Quit"
        ]
        
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.sample_rate = 16000
        self.stream = None
        self.model = None
        self.model_size = "tiny"
        self.auto_paste = True
        self.is_loading = False  # NEW: Flag to prevent multiple load attempts
        self.hotkey = None
        
        # Start loading model once
        self.load_model()
        
        # Setup keyboard listener
        self.setup_hotkeys()
        
        logging.info("App initialized")
    
    def load_model(self):
        """Load Whisper model at startup (ONCE)"""
        if self.is_loading:
            logging.info("Model already loading, skipping...")
            return
            
        self.is_loading = True
        
        def _load():
            try:
                from faster_whisper import WhisperModel
                
                self.menu["Status: Starting up..."] = "Status: Loading model..."
                logging.info(f"Loading {self.model_size} model...")
                
                self.model = WhisperModel(
                    self.model_size,
                    device="cpu",
                    compute_type="int8",
                    download_root=str(Path.home() / ".cache" / "whisper"),
                    num_workers=1
                )
                
                self.menu["Status: Loading model..."] = "Status: Ready"
                self.is_loading = False
                logging.info("Model loaded successfully")
                rumps.notification("🎤", "Ready", "Model loaded - ready to transcribe")
                
            except Exception as e:
                logging.error(f"Failed to load model: {e}")
                self.menu["Status: Loading model..."] = "Status: Error"
                self.is_loading = False
                rumps.alert("Model Error", f"Could not load Whisper model: {e}")
        
        threading.Thread(target=_load).start()
    
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        try:
            def on_activate():
                """Toggle recording on/off"""
                if self.is_recording:
                    self.stop_recording_action()
                else:
                    self.start_recording_action()
            
            # Create hotkey for Command + Shift + Space
            self.hotkey = keyboard.GlobalHotKeys({
                '<cmd>+<shift>+space': on_activate
            })
            self.hotkey.start()
            logging.info("Hotkey registered: Cmd+Shift+Space")
            
        except Exception as e:
            logging.error(f"Failed to setup hotkeys: {e}")
    
    @rumps.clicked("Start Recording")
    def start_recording_menu(self, _):
        self.start_recording_action()
    
    def start_recording_action(self):
        """Start recording audio"""
        if self.is_recording:
            return
        
        # Check if model is loaded
        if self.model is None:
            if self.is_loading:
                rumps.notification("🎤", "Please Wait", "Model still loading...")
            else:
                # Try loading again if it failed
                self.load_model()
                rumps.notification("🎤", "Loading", "Starting model load...")
            return
            
        self.is_recording = True
        self.audio_queue = queue.Queue()
        
        def callback(indata, frames, time, status):
            if status:
                logging.warning(f"Status: {status}")
            self.audio_queue.put(indata.copy())
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=callback,
                dtype='float32',
                blocksize=1024
            )
            self.stream.start()
            self.menu["Status: Ready"] = "Status: Recording..."
            rumps.notification("🎤", "Recording", "Started - speak now")
            logging.info("Recording started")
        except Exception as e:
            logging.error(f"Failed to start: {e}")
            self.is_recording = False
    
    @rumps.clicked("Stop Recording")
    def stop_recording_menu(self, _):
        self.stop_recording_action()
    
    def stop_recording_action(self):
        """Stop recording and transcribe"""
        if not self.is_recording:
            return
        
        # Stop recording first
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        self.menu["Status: Recording..."] = "Status: Transcribing..."
        rumps.notification("🎤", "Processing", "Transcribing your speech...")
        logging.info("Recording stopped, starting transcription")
        
        # Collect audio immediately
        audio_chunks = []
        while not self.audio_queue.empty():
            audio_chunks.append(self.audio_queue.get())
        
        if not audio_chunks:
            self.menu["Status: Transcribing..."] = "Status: Ready"
            rumps.notification("🎤", "No Audio", "No speech detected")
            return
        
        # Combine chunks
        audio = np.concatenate(audio_chunks, axis=0)
        
        # Transcribe in background
        threading.Thread(target=self.transcribe_audio, args=(audio,)).start()
    
    def transcribe_audio(self, audio):
        """Transcribe recorded audio"""
        try:
            # Save to temp file
            temp_dir = Path(tempfile.gettempdir()) / "speech2text"
            temp_dir.mkdir(exist_ok=True)
            temp_file = temp_dir / f"recording_{int(time.time())}.wav"
            
            import scipy.io.wavfile as wav
            wav.write(str(temp_file), self.sample_rate, audio)
            logging.info(f"Saved audio: {temp_file}")
            
            # Transcribe (model should already be loaded)
            logging.info("Starting Whisper transcription...")
            segments, info = self.model.transcribe(
                str(temp_file),
                beam_size=5,
                language="en",
                vad_filter=True,
                without_timestamps=True
            )
            
            # Collect text
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
                logging.debug(f"Segment: {segment.text}")
            
            full_text = " ".join(text_parts)
            
            if full_text.strip():
                if self.auto_paste:
                    pasted = self.paste_text(full_text)
                    if pasted:
                        rumps.notification(
                            "✅ Speech2Text",
                            "Auto-Pasted!",
                            f"'{full_text[:30]}...'"
                        )
                    else:
                        pyperclip.copy(full_text)
                        rumps.notification(
                            "📋 Speech2Text",
                            "Copied to Clipboard",
                            f"'{full_text[:30]}...'\n\nPress Cmd+V to paste"
                        )
                else:
                    pyperclip.copy(full_text)
                    rumps.notification(
                        "📋 Speech2Text",
                        "Copied to Clipboard",
                        f"'{full_text[:30]}...'\n\nPress Cmd+V to paste"
                    )
                
                logging.info(f"Transcribed: {full_text[:50]}...")
            else:
                rumps.notification("🎤", "No Speech", "Could not detect speech")
            
            # Clean up
            try:
                temp_file.unlink()
            except:
                pass
            
            self.menu["Status: Transcribing..."] = "Status: Ready"
            
        except Exception as e:
            logging.error(f"Transcription error: {e}", exc_info=True)
            self.menu["Status: Transcribing..."] = "Status: Error"
            rumps.alert("Error", f"Transcription failed: {e}")
    
    def paste_text(self, text):
        """Paste text at cursor location"""
        try:
            original = pyperclip.paste()
            pyperclip.copy(text)
            time.sleep(0.1)
            
            script = '''
            tell application "System Events"
                keystroke "v" using command down
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True)
            
            if result.returncode == 0:
                threading.Timer(0.5, lambda: pyperclip.copy(original)).start()
                logging.info("Text pasted successfully")
                return True
            else:
                logging.error(f"Paste script failed: {result.stderr}")
                return False
            
        except Exception as e:
            logging.error(f"Paste failed: {e}")
            return False
    
    @rumps.clicked("Auto-Paste: ON")
    @rumps.clicked("Auto-Paste: OFF")
    def toggle_auto_paste(self, sender):
        self.auto_paste = not self.auto_paste
        new_state = "ON" if self.auto_paste else "OFF"
        self.menu[sender.title] = f"Auto-Paste: {new_state}"
        rumps.notification("🎤", "Auto-Paste", f"Turned {new_state}")
        logging.info(f"Auto-paste toggled to {new_state}")
    
    @rumps.clicked("Model: tiny")
    @rumps.clicked("Model: base")
    @rumps.clicked("Model: small")
    @rumps.clicked("Model: medium")
    def cycle_model(self, sender):
        models = ["tiny", "base", "small", "medium"]
        current = self.model_size
        next_index = (models.index(current) + 1) % len(models)
        self.model_size = models[next_index]
        self.menu[f"Model: {current}"] = f"Model: {self.model_size}"
        
        # Reload model with new size
        self.model = None
        self.load_model()  # This will now respect the is_loading flag
        
        rumps.notification("🎤", "Model Changed", f"Loading {self.model_size} model...")
        logging.info(f"Model changed to {self.model_size}")
    
    @rumps.clicked("Quit")
    def quit(self, _):
        logging.info("Quitting")
        if self.hotkey:
            self.hotkey.stop()
        cleanup_lock()
        rumps.quit_application()

if __name__ == "__main__":
    app = Speech2TextApp()
    try:
        app.run()
    finally:
        cleanup_lock()

"""
# 4. Rebuild with ONLY the correct imports
pyinstaller --windowed \
            --name "Speech2Text Pro" \
            --add-data "src:src" \
            --hidden-import rumps \
            --hidden-import sounddevice \
            --hidden-import numpy \
            --hidden-import scipy \
            --hidden-import pyperclip \
            --hidden-import faster_whisper \
            --hidden-import pynput \
            --collect-all faster_whisper \
            src/main.py

# 5. Run the freshly built app
./dist/Speech2Text\ Pro.app/Contents/MacOS/Speech2Text\ Pro
"""