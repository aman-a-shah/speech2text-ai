from global_hotkeys import register_hotkeys, start_looping
import threading

class HotkeyManager:
    def __init__(self, on_start_callback, on_stop_callback):
        self.on_start = on_start_callback
        self.on_stop = on_stop_callback
        self.is_listening = False
        
    def setup_hotkeys(self):
        """Register global hotkeys [citation:3]"""
        hotkeys = [
            [["control", "win"], "start", self.on_start_callback],
            [["control"], "stop", self.on_stop_callback],
            [["alt"], "auto_send", self.on_auto_send],
            [["esc"], "cancel", self.on_cancel],
        ]
        register_hotkeys(hotkeys)
        
    def start(self):
        """Start hotkey listener thread"""
        self.setup_hotkeys()
        thread = threading.Thread(target=start_looping)
        thread.daemon = True
        thread.start()
        
    def on_start_callback(self):
        print("Hotkey pressed: Start recording")
        self.on_start()
        
    def on_stop_callback(self):
        print("Hotkey pressed: Stop and transcribe")
        self.on_stop()
        
    def on_auto_send(self):
        print("Hotkey pressed: Stop and auto-send with Enter")
        self.on_stop(auto_send=True)
        
    def on_cancel(self):
        print("Hotkey pressed: Cancel recording")
        # Implement cancellation