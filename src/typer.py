import pyperclip
import time
import platform

class TextTyper:
    def __init__(self):
        self.system = platform.system()
        
    def type_text(self, text: str, auto_enter: bool = False):
        """
        Type text at current cursor position
        """
        # Save current clipboard content [citation:3]
        original_clipboard = pyperclip.paste()
        
        try:
            # Copy text to clipboard
            pyperclip.copy(text)
            
            # Simulate paste command
            self._simulate_paste()
            
            # Optional: Press Enter
            if auto_enter:
                self._simulate_enter()
                
        finally:
            # Restore original clipboard after short delay
            time.sleep(0.1)
            pyperclip.copy(original_clipboard)
            
    def _simulate_paste(self):
        """Simulate Ctrl+V (Windows/Linux) or Cmd+V (macOS)"""
        if self.system == "Windows":
            self._send_keys([17], 'v')  # Ctrl+V
        elif self.system == "Darwin":  # macOS
            self._send_keys([56], 'v')  # Cmd+V
        else:  # Linux
            self._send_keys([29], 'v')  # Ctrl+V (varies by WM)
            
    def _simulate_enter(self):
        """Simulate Enter key press"""
        self._send_keys([], '\n')
        
    def _send_keys(self, modifiers, key):
        """Platform-specific key simulation"""
        if self.system == "Windows":
            self._windows_send_keys(modifiers, key)
        elif self.system == "Darwin":
            self._macos_send_keys(modifiers, key)
        else:
            self._linux_send_keys(modifiers, key)
            
    def _windows_send_keys(self, modifiers, key):
        """Windows implementation using win32api"""
        import win32api
        import win32con
        
        # Press modifiers
        for mod in modifiers:
            win32api.keybd_event(mod, 0, 0, 0)
            
        # Press key
        win32api.keybd_event(ord(key.upper()), 0, 0, 0)
        
        # Release in reverse order
        win32api.keybd_event(ord(key.upper()), 0, win32con.KEYEVENTF_KEYUP, 0)
        for mod in reversed(modifiers):
            win32api.keybd_event(mod, 0, win32con.KEYEVENTF_KEYUP, 0)
            
    def _macos_send_keys(self, modifiers, key):
        """macOS implementation using pyobjc"""
        from Quartz import CGEventCreateKeyboardEvent, CGEventPostToPid
        # Implementation using Quartz events
        pass
        
    def _linux_send_keys(self, modifiers, key):
        """Linux implementation using X11"""
        from Xlib import X, display
        from Xlib.ext.xtest import fake_input
        # Implementation using XTest
        pass