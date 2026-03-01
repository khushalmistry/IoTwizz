#!/bin/bash
#
# IoTwizz Binary Builder
# Builds standalone binaries for all platforms
#
# This script requires:
#   - Python 3.8+
#   - PyInstaller (pip install pyinstaller)
#   - Network access to install dependencies
#

set -e

echo "
╔══════════════════════════════════════════════════════════════╗
║              IoTwizz Binary Builder                          ║
╚══════════════════════════════════════════════════════════════╝
"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Install PyInstaller if needed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Get version
VERSION=$(python3 -c "from iotwizz import __version__; print(__version__)")
echo "   Version: $VERSION"

# Detect current platform
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64|amd64) ARCH="x64" ;;
    arm64|aarch64) ARCH="arm64" ;;
esac

echo "   Platform: $OS-$ARCH"
echo ""

# Build binary
echo "🔨 Building binary..."
pyinstaller --name iotwizz \
    --onefile \
    --console \
    --clean \
    --noconfirm \
    --add-data "data:data" \
    --add-data "iotwizz:iotwizz" \
    --hidden-import paho.mqtt.client \
    --hidden-import paho.mqtt.enums \
    --hidden-import google.generativeai \
    --hidden-import openai \
    --hidden-import anthropic \
    --hidden-import bleak \
    --hidden-import bleak.backends \
    --hidden-import bleak.backends.corebluetooth \
    --hidden-import bleak.backends.scanner \
    --hidden-import serial \
    --hidden-import serial.tools \
    --hidden-import serial.tools.list_ports \
    --hidden-import paramiko \
    --hidden-import scapy \
    --hidden-import prompt_toolkit \
    --hidden-import prompt_toolkit.input \
    --hidden-import prompt_toolkit.output \
    --hidden-import rich \
    --collect-all paho \
    --collect-all prompt_toolkit \
    --collect-all rich \
    iotwizz/main.py

# Rename binary with platform suffix
if [ -f "dist/iotwizz" ]; then
    if [ "$OS" = "darwin" ]; then
        OUTPUT_NAME="iotwizz-macos-$ARCH"
    elif [ "$OS" = "linux" ]; then
        OUTPUT_NAME="iotwizz-linux-$ARCH"
    else
        OUTPUT_NAME="iotwizz-$OS-$ARCH"
    fi
    
    mv dist/iotwizz "dist/$OUTPUT_NAME"
    
    # Create zip archive
    cd dist
    zip -r "${OUTPUT_NAME}.zip" "$OUTPUT_NAME"
    
    # Generate checksum
    if command -v sha256sum &> /dev/null; then
        sha256sum "${OUTPUT_NAME}.zip" > "${OUTPUT_NAME}.sha256"
    else
        shasum -a 256 "${OUTPUT_NAME}.zip" > "${OUTPUT_NAME}.sha256"
    fi
    
    cd ..
    
    echo ""
    echo "✅ Build complete!"
    echo ""
    echo "   Binary: dist/$OUTPUT_NAME"
    echo "   Archive: dist/${OUTPUT_NAME}.zip"
    echo "   Checksum: dist/${OUTPUT_NAME}.sha256"
    echo ""
    ls -lh dist/
    echo ""
    echo "🚀 Test the binary:"
    echo "   ./dist/$OUTPUT_NAME --version"
    echo "   ./dist/$OUTPUT_NAME --help"
else
    echo "❌ Build failed!"
    exit 1
fi
