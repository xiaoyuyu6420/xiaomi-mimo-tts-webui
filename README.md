# Xiaomi MiMo TTS Voice Clone

A web-based voice cloning application powered by Xiaomi's MiMo-V2.5-TTS API. Upload reference audio, type text, and generate speech that mimics the reference voice.

## Features

- **Voice Cloning** - Clone any voice from reference audio using MiMo-V2.5-TTS-voiceclone
- **Multi-Reference Upload** - Upload and merge multiple audio files for better cloning quality
- **Fine-Grained Control** - Adjust temperature, top_p, seed, and batch count
- **Preset Modes** - Stable / Balanced / Creative one-click presets
- **Emotion Tags** - Insert emotion markers like (Happy), (Sad), (Angry) into text
- **Provider Selection** - Switch between MiMo Official and Token Plan endpoints, or use a custom endpoint
- **Remember Settings** - API Key and endpoint saved in browser localStorage
- **Cross-Platform** - Works on Windows, Linux, and macOS

## Quick Start

### Option 1: Download EXE (No Python Required)

Download the latest `.exe` from [Releases](https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui/releases) and double-click to run.

> Requires [ffmpeg](https://ffmpeg.org/download.html) for MP3 support (WAV works without it).

### Option 2: Run with Python

**Windows:**
```
Double-click start.bat
```

**Linux / macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Or manually:**
```bash
git clone https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui.git
cd xiaomi-mimo-tts-webui
pip install -r requirements.txt
python app.py
```

Open http://localhost:7860 in your browser.

### Prerequisites

- Python 3.9+ (not needed for EXE version)
- [ffmpeg](https://ffmpeg.org/download.html) (for MP3 support; WAV works without it)
- A MiMo API Key from [platform.xiaomimimo.com](https://platform.xiaomimimo.com)

## Usage

1. **Enter API Key** - Get one from [platform.xiaomimimo.com](https://platform.xiaomimimo.com)
2. **Select Endpoint** - Choose MiMo Official or Token Plan CN
3. **Upload Reference Audio** - Drag & drop or click to upload (mp3/wav, multiple files supported)
4. **Configure Parameters** - Use presets or manually adjust temperature/top_p/seed
5. **Enter Text** - Type the text you want to synthesize, add emotion tags if desired
6. **Generate** - Click "Generate Voice" and download the result

## Parameters Guide

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| temperature | 0 - 1.5 | 0.6 | Lower = more consistent and stable |
| top_p | 0.01 - 1.0 | 0.95 | Lower = more deterministic |
| seed | integer | random | Fixed seed for reproducible output |

### Preset Modes

| Mode | Temperature | Top P | Use Case |
|------|-------------|-------|----------|
| Stable | 0.2 | 0.7 | Consistent, predictable output |
| Balanced | 0.5 | 0.85 | General purpose |
| Creative | 0.8 | 0.95 | More expressive, varied output |

## Emotion Tags

Insert these tags into your text to control emotion and pacing:

`(Happy)` `(Sad)` `(Angry)` `(Gentle)` `(Low voice)` `(Sigh)` `(Laugh)` `(Whisper)` `(Crying)` `(Faster)` `(Pause)` `(Deep breath)`

Example: `Hello! (Happy) How are you today? (Pause) I missed you.`

## API Providers

| Provider | Base URL | Description |
|----------|----------|-------------|
| MiMo Official | `https://api.xiaomimimo.com/v1` | Direct access via Xiaomi platform |
| Token Plan CN | `https://token-plan-cn.xiaomimimo.com/v1` | Token plan endpoint |
| Custom | User-defined | Any OpenAI-compatible endpoint |

## Project Structure

```
xiaomi-mimo-tts-webui/
├── app.py              # Main application (Flask + inline frontend)
├── mimo_tts_example.py # API usage examples
├── requirements.txt    # Python dependencies
├── start.bat           # Windows one-click launcher
├── start.sh            # Linux/macOS one-click launcher
├── build.py            # Build script for generating .exe
├── LICENSE             # MIT License
└── README.md           # This file
```

## Tech Stack

- **Backend**: Python, Flask, OpenAI SDK
- **Frontend**: Vanilla HTML/CSS/JS (single-file SPA)
- **Audio Processing**: pydub (for multi-file concatenation)
- **API**: MiMo-V2.5-TTS (OpenAI-compatible format)

## Known Limitations

- Reference audio must be under 10MB (after merging)
- Supports mp3 and wav formats only
- Voice cloning quality depends on reference audio quality and length
- API is currently free for a limited time (as of 2026)

## License

[MIT License](LICENSE)

## Links

- [MiMo API Platform](https://platform.xiaomimimo.com)
- [MiMo TTS Documentation](https://platform.xiaomimimo.com/docs/usage-guide/speech-synthesis-v2.5)
- [Report Issues](https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui/issues)
