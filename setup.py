from setuptools import setup

APP = ['src/main.py']
DATA_FILES = [('assets', ['assets/icon.icns'])]
OPTIONS = {
    'argv_emulation': False,
    'packages': ['rumps', 'pystray', 'sounddevice'],
    'plist': {
        'CFBundleName': 'Speech2Type',
        'CFBundleDisplayName': 'Speech2Type',
        'CFBundleIdentifier': 'com.yourname.speech2type',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,  # LSUIElement=True makes it a menu bar app
        'NSMicrophoneUsageDescription': 'Speech2Type needs microphone access for voice typing',
        'NSDesktopFolderUsageDescription': 'Speech2Type needs accessibility access to type text',
    },
    'iconfile': 'assets/icon.icns',
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)