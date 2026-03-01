#!/bin/bash
#
# IoTwizz Setup Script
# Run this script after cloning the repository
#

set -e

echo "
╔══════════════════════════════════════════════════════════════╗
║                    IoTwizz Setup                             ║
║              The Hardware Hacker's Playbook                  ║
╚══════════════════════════════════════════════════════════════╝
"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.8+ is required. You have $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python version: $PYTHON_VERSION"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Install the package
echo ""
echo "📦 Installing IoTwizz..."
pip3 install -e .

# Create user directories
echo ""
echo "📁 Creating user directories..."
mkdir -p ~/.iotwizz/logs

# Check optional dependencies
echo ""
echo "🔍 Checking optional dependencies..."

check_command() {
    if command -v $1 &> /dev/null; then
        echo "  ✓ $1 installed"
        return 0
    else
        echo "  ⚠ $1 not installed (optional, for $2)"
        return 1
    fi
}

check_command binwalk "firmware analysis"
check_command openocd "JTAG/SWD debugging"
check_command flashrom "SPI flash operations"

# Success
echo ""
echo "╔══════════════════════════════════════════════════════════════╗
║                    Setup Complete!                           ║
╚══════════════════════════════════════════════════════════════╝
"
echo ""
echo "🚀 Quick Start:"
echo ""
echo "   iotwizz                    # Launch interactive console"
echo "   iotwizz --version          # Show version"
echo "   iotwizz --help             # Show help"
echo ""
echo "📚 Inside the console:"
echo ""
echo "   show modules               # List all modules"
echo "   use uart/baud_rate_finder  # Select a module"
echo "   set PORT /dev/ttyUSB0      # Configure options"
echo "   run                        # Execute module"
echo ""
echo "🤖 AI Assistant (AiWizz):"
echo ""
echo "   use ai/aiwizz              # Load AI assistant"
echo "   set PROVIDER gemini        # Choose AI provider"
echo "   set API_KEY your_key       # Set API key
   run                         # Start chatting"
echo ""
echo "🔨 Build standalone binary:"
echo ""
echo "   ./scripts/build.sh current    # Build for current platform"
echo "   make build                    # Alternative using Make"
echo ""
