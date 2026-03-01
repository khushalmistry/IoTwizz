# Building IoTwizz Binaries

This guide explains how to build standalone binaries for IoTwizz on different platforms.

## Quick Start

### Build for Current Platform

```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build
python build.py --build

# Or using Make
make build
```

### Build Using Shell Script

```bash
./scripts/build.sh current
```

## Platform-Specific Builds

### macOS (Apple Silicon - ARM64)

```bash
make build-mac
# Output: dist/iotwizz-macos-arm64
```

### macOS (Intel - x64)

Run on an Intel Mac:
```bash
make build-mac
# Output: dist/iotwizz-macos-x64
```

### Linux x64

```bash
make build-linux
# Output: dist/iotwizz-linux-x64
```

### Windows x64

On Windows with Python installed:
```cmd
pip install -r requirements.txt
pip install pyinstaller
python build.py --build
```
Output: `dist/iotwizz.exe`

## Docker Builds (Cross-Platform)

### Build Linux x64 Binary

```bash
docker build -t iotwizz-builder-linux -f Dockerfile.linux-x64 .
docker create --name iotwizz-temp iotwizz-builder-linux
docker cp iotwizz-temp:/output/iotwizz-linux-x64 dist/
docker rm iotwizz-temp
```

### Build All Platforms (macOS required for Mac binaries)

```bash
# Use GitHub Actions for automated builds
# See .github/workflows/build.yml
```

## GitHub Actions (Automated Builds)

Push a tag to trigger automated builds for all platforms:

```bash
git tag v1.1.0
git push origin v1.1.0
```

This will create binaries for:
- Linux x64
- Linux ARM64  
- macOS x64 (Intel)
- macOS ARM64 (Apple Silicon)
- Windows x64
- Windows ARM64

## Build Requirements

- Python 3.8+
- PyInstaller 6.0+
- All dependencies from requirements.txt

## Build Output

All binaries are placed in the `dist/` directory:

```
dist/
├── iotwizz                    # Current platform
├── iotwizz-macos-arm64        # macOS Apple Silicon
├── iotwizz-macos-x64          # macOS Intel
├── iotwizz-linux-x64          # Linux x86_64
├── iotwizz-linux-arm64        # Linux ARM64
├── iotwizz-windows-x64.exe    # Windows x64
└── iotwizz-windows-arm64.exe  # Windows ARM64
```

## Testing Binary

```bash
# After building
./dist/iotwizz --version
./dist/iotwizz --help

# Run interactive console
./dist/iotwizz
```

## Troubleshooting

### "Module not found" errors
Add hidden imports to the PyInstaller command:
```bash
--hidden-import module_name
```

### "Cannot find data files"
Ensure data files are included:
```bash
--add-data "data:data"
```

### Binary too large
This is normal for Python applications. The binary includes:
- Python interpreter
- All dependencies
- Data files

### Permission denied on Linux/macOS
```bash
chmod +x dist/iotwizz-*
```

## Distribution

Create release archives:

```bash
make package
# Creates .zip files in dist/
```

## Checksums

Generate checksums for verification:

```bash
cd dist
sha256sum *.zip > checksums.sha256
```
