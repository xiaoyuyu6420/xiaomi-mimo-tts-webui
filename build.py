"""
Build script - packages the app into a standalone .exe
Usage: python build.py
"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("  Building Xiaomi MiMo TTS Voice Clone .exe")
print("=" * 50)
print()

# Ensure dependencies are installed
print("[1/2] Installing dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyinstaller"])

# Build exe
print("[2/2] Packaging .exe...")
subprocess.check_call([
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--noconsole",
    "--name", "MiMo-TTS-Voice-Clone",
    "--add-data", "requirements.txt;.",
    "--hidden-import", "pydub",
    "--hidden-import", "pydub.audio_segment",
    "app.py",
])

print()
print("=" * 50)
print("  Build complete!")
print("  exe location: dist/MiMo-TTS-Voice-Clone.exe")
print("=" * 50)
