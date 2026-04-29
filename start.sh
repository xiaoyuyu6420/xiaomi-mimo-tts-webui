#!/bin/bash
# Xiaomi MiMo TTS Voice Clone - One-click launcher for Linux/macOS

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "=========================================="
echo "  Xiaomi MiMo TTS Voice Clone"
echo "=========================================="
echo ""

# Check Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}Error: Python 3.9+ is required but not found.${NC}"
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi

echo -e "${GREEN}Using Python: $PYTHON ($($PYTHON --version))${NC}"

# Check ffmpeg (needed by pydub for mp3 support)
if ! command -v ffmpeg &>/dev/null; then
    echo -e "${YELLOW}Warning: ffmpeg not found. MP3 files may not work.${NC}"
    echo "Install with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
    echo ""
fi

# Setup virtual environment
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install dependencies
echo "Checking dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo ""
echo -e "${GREEN}Starting server...${NC}"
echo "Open http://localhost:7860 in your browser"
echo "Press Ctrl+C to stop"
echo ""

# Auto-open browser (best effort)
if command -v open &>/dev/null; then
    (sleep 2 && open "http://localhost:7860") &
elif command -v xdg-open &>/dev/null; then
    (sleep 2 && xdg-open "http://localhost:7860") &
fi

python app.py
