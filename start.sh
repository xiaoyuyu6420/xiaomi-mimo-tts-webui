#!/bin/bash
# Xiaomi MiMo TTS Voice Clone - Quick launcher for Linux/macOS

set -e
cd "$(dirname "$0")"

echo "=========================================="
echo "  Xiaomi MiMo TTS Voice Clone"
echo "=========================================="
echo ""

# Check Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Error: Python not found. Install Python 3.9+ or use the .exe version."
    exit 1
fi

# Install missing deps silently
pip install -q openai flask pydub 2>/dev/null || "$PYTHON" -m pip install -q openai flask pydub 2>/dev/null

# Auto-open browser
if command -v open &>/dev/null; then
    (sleep 2 && open "http://localhost:7860") &
elif command -v xdg-open &>/dev/null; then
    (sleep 2 && xdg-open "http://localhost:7860") &
fi

echo "Starting server at http://localhost:7860"
echo "Press Ctrl+C to stop"
echo ""

"$PYTHON" app.py
