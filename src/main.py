#!/usr/bin/env python3
import sys
import os
import logging
from pathlib import Path

# Set up logging
log_dir = Path.home() / ".local" / "share" / "speech2type" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=log_dir / "app.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SpeechToTypeApp:
    # ... your existing app code ...
    
    def run(self):
        """Main entry point"""
        try:
            logging.info("Starting Speech2Type app")
            self.setup_tray()
            # Keep the app running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logging.info("App stopped by user")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Fatal error: {e}")
            sys.exit(1)

def main():
    """Entry point for the application"""
    app = SpeechToTypeApp()
    app.run()

if __name__ == "__main__":
    main()