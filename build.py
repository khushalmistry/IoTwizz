#!/usr/bin/env python3
"""
IoTwizz Build Script
Create standalone binaries for Linux, macOS, and Windows (x64 and ARM64).
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Configuration
APP_NAME = "iotwizz"
VERSION = "1.0.0"
AUTHOR = "Khushal Mistry"
DESCRIPTION = "IoTwizz - The Hardware Hacker's Playbook"

# PyInstaller options
PYINSTALLER_OPTS = [
    "--name", APP_NAME,
    "--onefile",
    "--console",
    "--clean",
    "--noconfirm",
    "--log-level", "WARN",
    # Hidden imports
    "--hidden-import", "paho.mqtt.client",
    "--hidden-import", "paho.mqtt.enums",
    "--hidden-import", "google.generativeai",
    "--hidden-import", "openai",
    "--hidden-import", "anthropic",
    "--hidden-import", "bleak",
    "--hidden-import", "bleak.backends",
    "--hidden-import", "bleak.backends.corebluetooth",
    "--hidden-import", "bleak.backends.scanner",
    "--hidden-import", "serial",
    "--hidden-import", "serial.tools",
    "--hidden-import", "serial.tools.list_ports",
    "--hidden-import", "paramiko",
    "--hidden-import", "scapy",
    "--hidden-import", "prompt_toolkit",
    "--hidden-import", "prompt_toolkit.input",
    "--hidden-import", "prompt_toolkit.output",
    "--hidden-import", "rich",
    # Data files
    "--add-data", "data:data",
    "--add-data", "iotwizz:iotwizz",
    # Collect all
    "--collect-all", "paho",
    "--collect-all", "prompt_toolkit",
    "--collect-all", "rich",
    # Entry point
    "iotwizz/main.py",
]


def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode == 0


def clean():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    
    dirs_to_remove = ["build", "dist", "__pycache__", "*.egg-info"]
    files_to_remove = ["*.spec"]
    
    for pattern in dirs_to_remove:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                print(f"  Removed: {path}")
    
    for pattern in files_to_remove:
        for path in Path(".").glob(pattern):
            if path.is_file():
                path.unlink()
                print(f"  Removed: {path}")
    
    # Remove __pycache__ from all subdirectories
    for path in Path(".").rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)
        print(f"  Removed: {path}")


def build_binary(target_platform=None):
    """Build a standalone binary using PyInstaller."""
    print(f"\n{'='*60}")
    print(f"Building IoTwizz {VERSION}")
    print(f"Platform: {target_platform or 'current'}")
    print(f"{'='*60}\n")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build the binary
    cmd = [sys.executable, "-m", "PyInstaller"] + PYINSTALLER_OPTS
    
    # Add platform-specific options
    if target_platform:
        if "linux" in target_platform.lower():
            cmd.extend(["--target-platform", "linux"])
        elif "darwin" in target_platform.lower() or "macos" in target_platform.lower():
            cmd.extend(["--target-platform", "darwin"])
        elif "windows" in target_platform.lower() or "win" in target_platform.lower():
            cmd.extend(["--target-platform", "windows"])
    
    print(f"\nRunning PyInstaller...")
    success = run_command(cmd)
    
    if success:
        binary_path = Path("dist") / APP_NAME
        if binary_path.exists():
            size_mb = binary_path.stat().st_size / (1024 * 1024)
            print(f"\n{'='*60}")
            print(f"✓ Build successful!")
            print(f"  Binary: {binary_path.absolute()}")
            print(f"  Size: {size_mb:.2f} MB")
            print(f"{'='*60}\n")
            return str(binary_path)
    
    print("\n✗ Build failed!")
    return None


def build_all_platforms():
    """Build binaries for all platforms (requires Docker)."""
    print("\n" + "="*60)
    print("Building for all platforms")
    print("="*60 + "\n")
    
    platforms = {
        "linux-x64": "Dockerfile.linux-x64",
        "linux-arm64": "Dockerfile.linux-arm64",
        "macos-x64": None,  # Requires macOS
        "macos-arm64": None,  # Requires Apple Silicon
        "windows-x64": "Dockerfile.windows-x64",
        "windows-arm64": None,  # Limited support
    }
    
    results = {}
    
    for platform, dockerfile in platforms.items():
        print(f"\n{'='*60}")
        print(f"Building for {platform}")
        print(f"{'='*60}\n")
        
        if dockerfile and os.path.exists(dockerfile):
            # Use Docker
            image_name = f"iotwizz-builder-{platform}"
            cmd = ["docker", "build", "-t", image_name, "-f", dockerfile, "."]
            if run_command(cmd):
                # Extract binary
                container_name = f"iotwizz-extract-{platform}"
                run_command(["docker", "create", "--name", container_name, image_name])
                run_command(["docker", "cp", f"{container_name}:/app/dist/.", "dist/"])
                run_command(["docker", "rm", container_name])
                results[platform] = "Built via Docker"
            else:
                results[platform] = "Docker build failed"
        elif dockerfile is None:
            results[platform] = "Requires native build environment"
        else:
            results[platform] = "Dockerfile not found"
    
    print("\n" + "="*60)
    print("Build Summary")
    print("="*60)
    for platform, status in results.items():
        print(f"  {platform}: {status}")
    print("="*60 + "\n")


def create_dockerfiles():
    """Create Dockerfiles for cross-platform builds."""
    
    # Linux x64
    linux_x64 = '''# IoTwizz Builder - Linux x64
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libffi-dev \\
    libssl-dev \\
    libusb-1.0-0-dev \\
    libudev-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pyinstaller

# Build
RUN pyinstaller --name iotwizz --onefile --console --clean \\
    --add-data "data:data" \\
    --add-data "iotwizz:iotwizz" \\
    --hidden-import paho.mqtt.client \\
    --hidden-import bleak \\
    --hidden-import serial \\
    --hidden-import paramiko \\
    --hidden-import scapy \\
    --hidden-import prompt_toolkit \\
    --hidden-import rich \\
    iotwizz/main.py

# Output
RUN mkdir -p /output && cp dist/iotwizz /output/iotwizz-linux-x64
'''
    
    # Linux ARM64
    linux_arm64 = '''# IoTwizz Builder - Linux ARM64
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libffi-dev \\
    libssl-dev \\
    libusb-1.0-0-dev \\
    libudev-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pyinstaller

# Build
RUN pyinstaller --name iotwizz --onefile --console --clean \\
    --add-data "data:data" \\
    --add-data "iotwizz:iotwizz" \\
    --hidden-import paho.mqtt.client \\
    --hidden-import bleak \\
    --hidden-import serial \\
    --hidden-import paramiko \\
    --hidden-import scapy \\
    --hidden-import prompt_toolkit \\
    --hidden-import rich \\
    iotwizz/main.py

# Output
RUN mkdir -p /output && cp dist/iotwizz /output/iotwizz-linux-arm64
'''
    
    # Windows x64
    windows_x64 = '''# IoTwizz Builder - Windows x64
FROM mcr.microsoft.com/windows/python:3.11

WORKDIR /app

# Copy project
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir pyinstaller

# Build
RUN pyinstaller --name iotwizz --onefile --console --clean \\
    --add-data "data;data" \\
    --add-data "iotwizz;iotwizz" \\
    --hidden-import paho.mqtt.client \\
    --hidden-import bleak \\
    --hidden-import serial \\
    --hidden-import paramiko \\
    --hidden-import scapy \\
    --hidden-import prompt_toolkit \\
    --hidden-import rich \\
    iotwizz/main.py

# Output
RUN mkdir C:\\output && copy dist\\iotwizz.exe C:\\output\\iotwizz-windows-x64.exe
'''

    # Write Dockerfiles
    dockerfiles = {
        "Dockerfile.linux-x64": linux_x64,
        "Dockerfile.linux-arm64": linux_arm64,
        "Dockerfile.windows-x64": windows_x64,
    }
    
    for name, content in dockerfiles.items():
        with open(name, 'w') as f:
            f.write(content)
        print(f"Created {name}")


def create_github_workflow():
    """Create GitHub Actions workflow for automated builds."""
    
    workflow_dir = Path(".github/workflows")
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    workflow = '''name: Build IoTwizz Binaries

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-linux:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        arch: [x64, arm64]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build binary
        run: python build.py --platform linux-${{ matrix.arch }}
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: iotwizz-linux-${{ matrix.arch }}
          path: dist/iotwizz

  build-macos:
    runs-on: macos-latest
    strategy:
      matrix:
        arch: [x64, arm64]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build binary
        run: python build.py
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: iotwizz-macos-${{ matrix.arch }}
          path: dist/iotwizz

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build binary
        run: python build.py
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: iotwizz-windows-x64
          path: dist/iotwizz.exe

  release:
    needs: [build-linux, build-macos, build-windows]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/')
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            iotwizz-linux-x64/iotwizz
            iotwizz-linux-arm64/iotwizz
            iotwizz-macos-x64/iotwizz
            iotwizz-macos-arm64/iotwizz
            iotwizz-windows-x64/iotwizz.exe
'''
    
    workflow_path = workflow_dir / "build.yml"
    with open(workflow_path, 'w') as f:
        f.write(workflow)
    
    print(f"Created {workflow_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="IoTwizz Build Script")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts")
    parser.add_argument("--build", action="store_true", help="Build for current platform")
    parser.add_argument("--all", action="store_true", help="Build for all platforms (requires Docker)")
    parser.add_argument("--platform", type=str, help="Target platform (linux-x64, linux-arm64, macos-x64, macos-arm64, windows-x64)")
    parser.add_argument("--dockerfiles", action="store_true", help="Create Dockerfiles for cross-platform builds")
    parser.add_argument("--github", action="store_true", help="Create GitHub Actions workflow")
    
    args = parser.parse_args()
    
    if args.clean:
        clean()
    
    if args.dockerfiles:
        create_dockerfiles()
    
    if args.github:
        create_github_workflow()
    
    if args.build:
        build_binary(args.platform)
    
    if args.all:
        build_all_platforms()
    
    if not any([args.clean, args.build, args.all, args.dockerfiles, args.github]):
        # Default: build for current platform
        build_binary()


if __name__ == "__main__":
    main()
