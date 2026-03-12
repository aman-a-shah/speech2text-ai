import sys
import threading
from pathlib import Path
import yaml
import os

from audio_recorder import AudioRecorder
from transcriber import Transcriber
from typer import TextTyper
import tkinter as tk
from tkinter import ttk

class SpeechToTypeApp:
    def __init__(self):
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(
            model_size=self.get_config("whisper.model", "tiny"),
            device=self.get_config("whisper.device", "cpu")
        )
        self.typer = TextTyper()
        
        # Load config
        self.config_path = Path.home() / ".config" / "speech2type" / "config.yaml"
        self.load_config()
        
        # Initialize hotkeys based on platform
        self.init_hotkeys()
        
        # Setup system tray
        self.setup_tray()
        
    def load_config(self):
        """Load configuration from YAML file [citation:3]"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self.default_config()
            self.save_config()
            
    def default_config(self):
        """Default configuration"""
        return {
            "whisper": {
                "model": "tiny",
                "device": "cpu",
                "compute_type": "int8",
                "language": "en"
            },
            "hotkey": {
                "start": "ctrl+win" if sys.platform == "win32" else "fn+ctrl",
                "stop": "ctrl" if sys.platform == "win32" else "fn",
                "auto_send": "alt" if sys.platform == "win32" else "option"
            },
            "vad": {
                "enabled": True,
                "threshold": 0.7,
                "silence_timeout": 30.0
            },
            "clipboard": {
                "auto_paste": True,
                "preserve_clipboard": True
            }
        }
        
    def get_config(self, key: str, default=None):
        """Get config value with dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
        
    def init_hotkeys(self):
        """Initialize platform-specific hotkeys"""
        if sys.platform == "win32":
            from hotkeys_windows import HotkeyManager
        elif sys.platform == "darwin":
            from hotkeys_macos import HotkeyManager
        else:
            from hotkeys_linux import HotkeyManager
            
        self.hotkeys = HotkeyManager(
            on_start_callback=self.start_recording,
            on_stop_callback=self.stop_and_transcribe
        )
        self.hotkeys.start()
        
    def start_recording(self):
        """Start recording callback"""
        print("Starting recording...")
        self.recorder.start_recording()
        # Update tray icon to show recording state
        
    def stop_and_transcribe(self, auto_send: bool = False):
        """Stop recording and transcribe"""
        print("Stopping recording...")
        audio = self.recorder.stop_recording()
        
        if len(audio) == 0:
            print("No audio recorded")
            return
            
        # Transcribe in background thread
        def transcribe_thread():
            text = self.transcriber.transcribe(audio)
            print(f"Transcribed: {text}")
            
            if text:
                self.typer.type_text(text, auto_send)
                
        threading.Thread(target=transcribe_thread).start()
        
    def setup_tray(self):
        """Setup system tray icon [citation:3]"""
        from pystray import Icon, Menu, MenuItem
        from PIL import Image, ImageDraw
        
        # Create icon
        image = Image.new('RGB', (64, 64), color='black')
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill='white')
        
        # Create menu
        menu = Menu(
            MenuItem('Settings', self.open_settings),
            MenuItem('Change Model', self.change_model),
            MenuItem('Exit', self.exit_app)
        )
        
        self.tray_icon = Icon("speech2type", image, "Speech2Type", menu)
        
        # Run tray in background thread
        threading.Thread(target=self.tray_icon.run).start()
        
    def open_settings(self):
        """Open settings window"""
        self.settings_window = SettingsWindow(self)
        
    def change_model(self):
        """Change Whisper model"""
        # Implementation
        pass
        
    def exit_app(self):
        """Exit application"""
        self.tray_icon.stop()
        sys.exit(0)

class SettingsWindow:
    def __init__(self, app):
        self.app = app
        self.window = tk.Tk()
        self.window.title("Speech2Type Settings")
        self.window.geometry("400x300")
        
        self.setup_ui()
        self.window.mainloop()
        
    def setup_ui(self):
        """Setup settings UI"""
        # Model selection
        ttk.Label(self.window, text="Model Size:").pack(pady=5)
        self.model_var = tk.StringVar(value=self.app.get_config("whisper.model"))
        model_combo = ttk.Combobox(
            self.window, 
            textvariable=self.model_var,
            values=["tiny", "base", "small", "medium"]
        )
        model_combo.pack(pady=5)
        
        # Language selection
        ttk.Label(self.window, text="Language:").pack(pady=5)
        self.lang_var = tk.StringVar(value=self.app.get_config("whisper.language", "en"))
        lang_entry = ttk.Entry(self.window, textvariable=self.lang_var)
        lang_entry.pack(pady=5)
        
        # Save button
        ttk.Button(
            self.window,
            text="Save",
            command=self.save_settings
        ).pack(pady=20)
        
    def save_settings(self):
        """Save settings to config"""
        self.app.config["whisper"]["model"] = self.model_var.get()
        self.app.config["whisper"]["language"] = self.lang_var.get()
        self.app.save_config()
        self.window.destroy()

if __name__ == "__main__":
    app = SpeechToTypeApp()