#!/usr/bin/env python3
"""
Complete end-to-end test for Whisper speech-to-text
Records from microphone and transcribes using Whisper
"""

import time
import numpy as np
import sounddevice as sd
import whisper
import warnings
import sys

# Suppress some warnings for cleaner output
warnings.filterwarnings("ignore")

print("=" * 50)
print("WHISPER SPEECH-TO-TEXT TEST")
print("=" * 50)

# Step 1: Check imports
print("\n📦 Step 1: Checking imports...")
try:
    import whisper
    print("  ✅ Whisper imported successfully")
except ImportError as e:
    print(f"  ❌ Whisper not installed: {e}")
    sys.exit(1)

try:
    import sounddevice as sd
    import numpy as np
    print("  ✅ Sounddevice and NumPy imported successfully")
except ImportError as e:
    print(f"  ❌ Sounddevice or NumPy not installed: {e}")
    sys.exit(1)

# Step 2: Check available audio devices
print("\n🎤 Step 2: Checking audio devices...")
try:
    devices = sd.query_devices()
    print(f"  ✅ Found {len(devices)} audio devices")
    
    # Show default input device
    default_input = sd.default.device[0]
    if default_input is None or default_input == -1:
        print("  ⚠️  No default input device found. Please check microphone.")
        print("  Available input devices:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"    [{i}] {device['name']}")
    else:
        input_device_info = sd.query_devices(default_input)
        print(f"  ✅ Default input device: [{default_input}] {input_device_info['name']}")
except Exception as e:
    print(f"  ❌ Error checking audio devices: {e}")
    sys.exit(1)

# Step 3: Load Whisper model
print("\n🤖 Step 3: Loading Whisper model...")
print("  (This downloads the model on first run - ~1GB for base model)")
try:
    # Use "tiny" for fastest testing, "base" for better accuracy
    model_size = "tiny"  # Change to "base" for better results
    print(f"  Loading '{model_size}' model...")
    model = whisper.load_model(model_size)
    print(f"  ✅ Whisper model '{model_size}' loaded successfully")
except Exception as e:
    print(f"  ❌ Failed to load Whisper model: {e}")
    sys.exit(1)

# Step 4: Test recording
print("\n🎙️ Step 4: Testing microphone recording...")
print("  Recording 3 seconds of audio...")
print("  Speak now! (say something like 'Hello world' or 'Testing 1 2 3')")

try:
    # Recording parameters
    duration = 3  # seconds
    sample_rate = 16000  # Whisper expects 16kHz
    
    # Show countdown
    for i in range(3, 0, -1):
        print(f"    Starting in {i}...", end='\r')
        time.sleep(1)
    print("    Recording NOW!      ")
    
    # Record audio
    recording = sd.rec(int(duration * sample_rate), 
                       samplerate=sample_rate, 
                       channels=1, 
                       dtype=np.float32)
    sd.wait()  # Wait until recording is finished
    print("  ✅ Recording complete!")
    
    # Check if audio has sound
    audio_level = np.abs(recording).mean()
    if audio_level < 0.001:
        print("  ⚠️  Very low audio level. Check your microphone.")
        print(f"     Average audio level: {audio_level:.6f}")
    else:
        print(f"  ✅ Audio level: {audio_level:.6f} (good)")
        
except Exception as e:
    print(f"  ❌ Recording failed: {e}")
    sys.exit(1)

# Step 5: Transcribe the recording
print("\n📝 Step 5: Transcribing audio...")
print("  Processing with Whisper (this may take a few seconds)...")

try:
    # Convert recording to mono if needed (it's already mono, but just in case)
    audio = recording.flatten()
    
    # Transcribe
    start_time = time.time()
    result = model.transcribe(audio, language="en")
    end_time = time.time()
    
    print(f"  ✅ Transcription complete in {end_time - start_time:.2f} seconds")
    print("\n" + "=" * 50)
    print("📝 TRANSCRIPTION RESULT:")
    print("=" * 50)
    print(f"  \"{result['text']}\"")
    print("=" * 50)
    
except Exception as e:
    print(f"  ❌ Transcription failed: {e}")
    sys.exit(1)

# Step 6: Test with a file (optional)
print("\n💾 Step 6: Optional - Save recording to file? (y/n)")
# Skip automatic file saving to keep it simple
print("  (Skipping file save for now - add code to save if needed)")

# Step 7: Summary
print("\n" + "=" * 50)
print("📊 TEST SUMMARY")
print("=" * 50)
print(f"✅ Imports: Successful")
print(f"✅ Audio device: {'OK' if 'default_input' in locals() else 'Check manually'}")
print(f"✅ Model loaded: {model_size}")
print(f"✅ Recording: {duration} seconds")
print(f"✅ Transcription: {'Success' if 'result' in locals() else 'Failed'}")
if 'result' in locals() and result['text'].strip():
    print(f"✅ Heard: \"{result['text'][:50]}...\"")
else:
    print("⚠️  No speech detected - try speaking louder or check microphone")
print("=" * 50)

# Bonus: Show next steps
print("\n🚀 NEXT STEPS:")
print("  • Try changing model_size to 'base' for better accuracy")
print("  • Increase duration for longer recordings")
print("  • Add hotkey support for global shortcuts")
print("  • Build the full desktop app with system tray integration")
print("=" * 50)