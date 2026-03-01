#!/bin/bash
#
# IoTwizz Build Script
# Builds standalone binaries for multiple platforms
#
# Usage: ./scripts/build.sh [platform]
# Platforms: macos-arm64, macos-x64, linux-x64, linux-arm64, windows-x64, all, current
#

set -e

# Configuration
VERSION="1.1.0"
APP_NAME="iotwizz"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$PROJECT_DIR/dist"
BUILD_DIR="$PROJECT_DIR/build"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    if ! python3 -c "import PyInstaller" 2>/dev/null; then
        log_warning "PyInstaller not found. Installing..."
        pip3 install pyinstaller || {
            log_error "Failed to install PyInstaller. Run: pip install pyinstaller"
            exit 1
        }
    fi
    
    log_success "Dependencies OK"
}

clean_build() {
    log_info "Cleaning build artifacts..."
    rm -rf "$BUILD_DIR" "$DIST_DIR"/*.spec 2>/dev/null || true
    mkdir -p "$DIST_DIR"
}

build_current() {
    local platform=$(uname -s | tr '[:upper:]' '[:lower:]')
    local arch=$(uname -m)
    
    log_info "Building for current platform: $platform-$arch"
    
    cd "$PROJECT_DIR"
    
    pyinstaller --name "$APP_NAME" \
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
    
    local output_name="$APP_NAME-$platform-$arch"
    if [[ "$platform" == "darwin" ]]; then
        output_name="$APP_NAME-macos-$arch"
    elif [[ "$platform" == "windows" ]]; then
        output_name="$APP_NAME-windows-$arch.exe"
    fi
    
    mv "$DIST_DIR/$APP_NAME" "$DIST_DIR/$output_name" 2>/dev/null || true
    
    log_success "Build complete: $DIST_DIR/$output_name"
    ls -lh "$DIST_DIR/$output_name"
}

show_help() {
    echo "
IoTwizz Build Script
====================

Usage: $0 [command]

Commands:
  current         Build for current platform
  macos-arm64     Build for macOS Apple Silicon
  macos-x64       Build for macOS Intel
  linux-x64       Build for Linux x86_64  
  linux-arm64     Build for Linux ARM64
  windows-x64     Build for Windows x64
  all             Build for all platforms
  clean           Clean build artifacts
  help            Show this help message

Current Platform: $(uname -s)-$(uname -m)
"
}

# Main
cd "$PROJECT_DIR"
mkdir -p "$DIST_DIR"

case "${1:-current}" in
    current)
        check_dependencies
        clean_build
        build_current
        ;;
    macos-arm64|macos-x64|linux-x64|linux-arm64|windows-x64)
        check_dependencies
        clean_build
        build_current
        ;;
    clean)
        clean_build
        rm -rf "$DIST_DIR"/*.spec
        log_success "Cleaned build artifacts"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
