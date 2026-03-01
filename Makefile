# IoTwizz Build Makefile
# Usage: make [target]

.PHONY: all clean build build-mac build-linux build-windows install-deps help

VERSION := 1.1.0
APP_NAME := iotwizz

help:
	@echo "IoTwizz Build System"
	@echo "===================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all          - Build binary for current platform"
	@echo "  build        - Build binary for current platform"
	@echo "  build-mac    - Build for macOS (both Intel and Apple Silicon)"
	@echo "  build-linux  - Build for Linux x64"
	@echo "  build-windows- Build for Windows x64"
	@echo "  build-all    - Build for all platforms (requires Docker)"
	@echo "  install-deps - Install Python dependencies"
	@echo "  install-build- Install build dependencies (PyInstaller)"
	@echo "  clean        - Remove build artifacts"
	@echo "  test         - Run basic tests"
	@echo "  package      - Create distribution archives"
	@echo ""
	@echo "Current Platform: $(shell uname -s)-$(shell uname -m)"

all: build

install-deps:
	pip install -r requirements.txt

install-build:
	pip install pyinstaller

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

build: clean
	@echo "Building for current platform..."
	pyinstaller --name $(APP_NAME) \
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
	@echo ""
	@echo "Build complete! Binary: dist/$(APP_NAME)"

build-mac: clean
	@echo "Building for macOS..."
	pyinstaller --name $(APP_NAME) \
		--onefile \
		--console \
		--clean \
		--noconfirm \
		--target-platform darwin \
		--add-data "data:data" \
		--add-data "iotwizz:iotwizz" \
		--hidden-import paho.mqtt.client \
		--hidden-import bleak \
		--hidden-import serial \
		--hidden-import paramiko \
		--hidden-import scapy \
		--hidden-import prompt_toolkit \
		--hidden-import rich \
		--hidden-import google.generativeai \
		--hidden-import openai \
		--hidden-import anthropic \
		iotwizz/main.py
	mv dist/$(APP_NAME) dist/$(APP_NAME)-macos-$(shell uname -m)

build-linux: clean
	@echo "Building for Linux x64..."
	pyinstaller --name $(APP_NAME) \
		--onefile \
		--console \
		--clean \
		--noconfirm \
		--target-platform linux \
		--add-data "data:data" \
		--add-data "iotwizz:iotwizz" \
		--hidden-import paho.mqtt.client \
		--hidden-import bleak \
		--hidden-import serial \
		--hidden-import paramiko \
		--hidden-import scapy \
		--hidden-import prompt_toolkit \
		--hidden-import rich \
		--hidden-import google.generativeai \
		--hidden-import openai \
		--hidden-import anthropic \
		iotwizz/main.py
	mv dist/$(APP_NAME) dist/$(APP_NAME)-linux-x64

build-windows: clean
	@echo "Building for Windows x64..."
	pyinstaller --name $(APP_NAME) \
		--onefile \
		--console \
		--clean \
		--noconfirm \
		--target-platform windows \
		--add-data "data;data" \
		--add-data "iotwizz;iotwizz" \
		--hidden-import paho.mqtt.client \
		--hidden-import bleak \
		--hidden-import serial \
		--hidden-import paramiko \
		--hidden-import scapy \
		--hidden-import prompt_toolkit \
		--hidden-import rich \
		--hidden-import google.generativeai \
		--hidden-import openai \
		--hidden-import anthropic \
		iotwizz/main.py
	mv dist/$(APP_NAME).exe dist/$(APP_NAME)-windows-x64.exe

test:
	@echo "Running basic tests..."
	python3 -c "import iotwizz; print('✓ IoTwizz imports successfully')"
	python3 -c "from iotwizz.module_loader import ModuleLoader; l = ModuleLoader(); print(f'✓ Loaded {l.count} modules')"

package:
	@echo "Creating distribution archives..."
	cd dist && \
	zip -r $(APP_NAME)-$(VERSION)-macos-arm64.zip $(APP_NAME)-macos-arm64 2>/dev/null || true && \
	zip -r $(APP_NAME)-$(VERSION)-macos-x64.zip $(APP_NAME)-macos-x64 2>/dev/null || true && \
	zip -r $(APP_NAME)-$(VERSION)-linux-x64.zip $(APP_NAME)-linux-x64 2>/dev/null || true && \
	zip -r $(APP_NAME)-$(VERSION)-windows-x64.zip $(APP_NAME)-windows-x64.exe 2>/dev/null || true
	@echo "Archives created in dist/"

# Docker-based cross-platform builds
docker-build-linux-x64:
	@echo "Building Linux x64 binary using Docker..."
	docker build -t iotwizz-builder-linux-x64 -f Dockerfile.linux-x64 .
	docker create --name iotwizz-temp-linux-x64 iotwizz-builder-linux-x64
	docker cp iotwizz-temp-linux-x64:/app/dist/iotwizz dist/iotwizz-linux-x64
	docker rm iotwizz-temp-linux-x64

docker-build-all: docker-build-linux-x64
	@echo "All Docker builds complete!"
