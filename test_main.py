#!/usr/bin/env python3
import rumps
import logging
from pathlib import Path

# Setup logging
log_dir = Path.home() / ".local" / "share" / "speech2text" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_dir / "test.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TestApp(rumps.App):
    def __init__(self):
        super(TestApp, self).__init__("TestApp")
        self.menu = ["Test Recording", "Quit"]
        logging.info("Test app started")
        
    @rumps.clicked("Test Recording")
    def test_recording(self, _):
        rumps.notification("Test", "Recording would start here", "Click Stop to transcribe")
        logging.info("Test recording clicked")
        
    @rumps.clicked("Quit")
    def quit_app(self, _):
        logging.info("Quitting")
        rumps.quit_application()

if __name__ == "__main__":
    TestApp().run()
