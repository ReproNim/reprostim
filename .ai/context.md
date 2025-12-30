# ReproStim Project AI Context/Memory File

## Project Overview

**ReproStim** is a comprehensive video capture and recording suite designed for neuroimaging and psychology experiments. It provides experimenters with a complete, high-fidelity audio-visual record of stimulus presentation during fMRI scanning sessions as part of the **ReproFlow** ecosystem for reproducible neuroimaging data collection.

### Core Mission
- Automatic capture of all audio/video stimuli presented to research subjects
- Integration with BIDS (Brain Imaging Data Structure) datasets
- Minimal effort required from end-users (runs silently in background)
- Enhanced experimental reproducibility and data loss prevention
- Recovery of experimental data in case of irregularities or scanner glitches

### Architecture Overview
```
Hardware Layer (Magewell USB Capture Device)
          ↓
Capture Services (C++ videocapture/screencapture)
          ↓
Python Analysis Tools (QR parsing, audio codes, video audit)
          ↓
BIDS Integration & Documentation
```

## Project Structure

### Main Directories

#### `src/reprostim/` - Python Package (Core)
Main Python package with CLI tools and analysis utilities.

**Key Modules:**
- **cli/** - Command-line interface (Click-based with DYMGroup for suggestions)
  - `entrypoint.py` - Main CLI dispatcher
  - `cmd_qr_parse.py` - Parse QR codes from `.mkv` videos (PARSE/INFO modes)
  - `cmd_timesync_stimuli.py` - PsychoPy integration for QR/audio code generation
  - `cmd_detect_noscreen.py` - Detect no-signal/rainbow frames with fixup capabilities
  - `cmd_list_displays.py` - List available GUI displays (cross-platform)
  - `cmd_monitor_displays.py` - Monitor display connection status with callbacks
  - `cmd_video_audit.py` - Comprehensive video analysis (incremental/full/force modes)
  - `cmd_split_video.py` - Split/slice videos to specific time ranges (see [spec-split-video.md](.ai/spec-split-video.md))
  - `cmd_echo.py` - Simple echo command for testing

- **qr/** - QR code processing and time synchronization
  - `qr_parse.py` - Parse `.mkv` files, extract QR codes, audio codes, metadata → JSONL
  - `timesync_stimuli.py` - PsychoPy-based MRI/BIRCH/Magewell synchronization
  - `disp_mon.py` - Cross-platform display monitoring (Linux/macOS/Windows)
  - `psychopy.py` - PsychoPy framework integration utilities
  - `video_audit.py` - Comprehensive video analysis with multiple audit sources
  - `split_video.py` - Video slicing/splitting functionality (see [spec-split-video.md](.ai/spec-split-video.md))

- **audio/** - Audio codec generation
  - `audiocodes.py` - FSK/NFE codecs with Reed-Solomon error correction
  - Supports PsychoPy audio backends (sounddevice, PTB)
  - CRC8 checksum implementation for data validation

- **capture/** - Video capture utilities
  - `nosignal.py` - Rainbow/no-signal frame detection (multi-algorithm: has_rainbow, has_rainbow2)
  - VideoInfo Pydantic model for structured metadata
  - Video fixup capabilities using ffmpeg for truncated/invalid-timing videos

#### `src/reprostim-capture/` - C++ Video Capture Suite
CMake-based C++ project with 3 main executables.

**Structure:**
```
src/reprostim-capture/
├── CMakeLists.txt           # Main build configuration (C++20)
├── capturelib/              # Core capture library
│   ├── include/reprostim/   # Headers (CaptureLib, CaptureLog, CaptureApp)
│   ├── src/                 # Implementation files
│   └── test/                # Catch2-based C++ tests
├── screencapture/           # Screen capture utility
├── videocapture/            # Magewell USB video capture
├── rectrigger/              # Trigger server/client
└── 3rdparty/                # Magewell SDK (versions 3.3.1.0 and 3.3.1.1313)
```

**Key Components:**
- **CaptureLib**: Core library with threading, REST API, ReproMon integration, logging
- **ScreenCapture**: Desktop/screen recording utility
- **VideoCapture**: Magewell USB device capture with configuration support
- **Dependencies**: libMWCapture (Magewell SDK), libusb, wxWidgets, portaudio

#### `tests/` - Test Suite
```
tests/
├── audio/
│   └── test_audiocodes.py   # Audio codec tests (CRC8)
└── data/
    ├── reprostim-videos/    # Test video samples
    └── nosignal/            # No-signal detection test data
```

**Testing Approach:**
- **Python**: pytest with pytest-cov (coverage), pytest-mock (mocking), pytest-xdist (parallel)
- **C++**: Catch2 framework (v2/v3 compatible)
- **CI/CD**: GitHub Actions workflows, container-based integration tests

#### `docs/` - Documentation
Sphinx + MyST (Markdown support) documentation.

**Structure:**
```
docs/source/
├── conf.py              # Sphinx configuration
├── index.rst            # Main documentation index
├── intro/               # Introduction docs
├── install/             # Installation guide (Markdown)
├── cli/                 # CLI command documentation (auto-generated)
├── api/                 # Auto-generated API reference
├── dev/                 # Development guide
├── notes/               # Technical notes (disp_mon, psychopy, VAAPI, ffmpeg)
├── changes/             # Changelog/release notes
└── _static/             # Static assets
```

**Special Features:**
- Auto-documentation via sphinx-click
- Mermaid diagram support
- Read the Docs integration (`.readthedocs.yaml`)
- SVG-based ReproFlow diagram
- Platform-specific notes (Linux, macOS, Windows)

#### `containers/` - Container Definitions
Docker and Singularity container support for deployment.

**Structure:**
```
containers/repronim-reprostim/
├── Dockerfile.repronim-reprostim
├── Singularity.repronim-reprostim
├── generate_container.sh    # Template generation
├── build_docker.sh
├── build_singularity.sh
├── run_reprostim.sh
├── build_reprostim.sh       # Install script (PsychoPy + reprostim)
└── README.md
```

**Container Strategy:**
- **Base**: Neurodebian (bookworm)
- **PsychoPy**: Version 2025.2.0 via psychopy_linux_installer
- **Python**: 3.10 with all optional dependencies
- **Modes**: CI/CD mode (install from worktree) vs default mode (install from PyPI)
- **Features**: Development overlay support for debugging

#### `tools/` - CI/CD and Configuration Scripts
```
tools/
├── ci/                      # CI/CD scripts
│   ├── build_reprostim_container.sh
│   ├── run_reprostim_container.sh
│   ├── test_reprostim_container.sh
│   ├── test_reprostim_timesync-stimuli.sh
│   └── test_reprostim_events.sh
└── reproiner-config.sh      # ReproInner configuration
```

## Technology Stack

### Python Dependencies
- **Click 8.1.7+**: CLI framework with did-you-mean suggestions
- **PsychoPy**: Psychology experiment framework (optional)
- **OpenCV (cv2) 4.9.0+**: Video processing and QR code detection
- **Pyzbar 0.1.9+**: QR code scanning
- **Pydantic 2.7.1+**: Data validation and serialization
- **Numpy 1.26.4+**: Numerical operations
- **SciPy 1.14.1+**: Signal processing
- **sounddevice 0.5.1+**: Audio I/O
- **pygame 2.6.1+**: Display monitoring
- **PyAudio 0.2.14+**: Audio interface
- **reedsolo 1.7.0+**: Reed-Solomon error correction
- **psutil**: System monitoring

### C++ Stack
- **C++20**: Modern C++ standard
- **CMake 3.10+**: Build system
- **Magewell SDK 3.3.1**: USB capture device API
- **Catch2**: C++ testing framework (v2/v3)
- **libusb**: USB device interaction

### Documentation & Testing
- **Sphinx + MyST**: Documentation generation
- **pytest**: Python testing framework
- **pytest-cov**: Code coverage
- **pytest-mock**: Test mocking
- **pytest-xdist**: Parallel test execution

## Installation Options

```bash
# Core package
pip install reprostim

# With audio codec support
pip install reprostim[audio]

# With display monitoring (platform-specific)
pip install reprostim[disp_mon]

# With PsychoPy integration
pip install reprostim[psychopy]

# Everything
pip install reprostim[all,disp_mon]
```

## Build Systems

### Python Package
```bash
# Build system: hatchling with versioningit
# Version source: Git tags → src/reprostim/_version.py
# Distribution: PyPI (reprostim) and Conda-Forge

pip install -e .
```

### C++ Build
```bash
cd src/reprostim-capture
mkdir build && cd build
cmake .. -DCTEST_ENABLED=ON
make
make test
sudo make install  # Installs to CMAKE_INSTALL_PREFIX/bin
```

### Container Build
```bash
cd containers/repronim-reprostim
./generate_container.sh
./build_docker.sh
# or
./build_singularity.sh
```

## Workflow and Data Flow

```
Live Experiment Session
    ↓
Magewell USB Capture Device (Hardware)
    ↓
reprostim-videocapture (C++) → Records .mkv videos
    ↓
reprostim timesync-stimuli (Python/PsychoPy)
    ├─ Generates QR codes on screen (video)
    └─ Generates audio codes (FSK/NFE)
    ↓
Recorded Videos contain: Video + QR codes + Audio codes
    ↓
reprostim qr-parse → Extract QR/audio metadata (JSONL)
    ↓
reprostim video-audit → Analyze all videos, generate videos.tsv
    ↓
reprostim detect-noscreen → Check for no-signal frames
    ↓
Integrated with BIDS datasets for archival
```

## Important Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python package configuration, dependencies, build metadata |
| `CMakeLists.txt` | C++ build configuration (reprostim-capture) |
| `README.md` | Project overview, quick start guide |
| `CHANGELOG.md` | Release notes and version history |
| `overview.md` | Detailed project scope and architecture |
| `src/reprostim/__init__.py` | Logger initialization, package entry point |
| `src/reprostim/cli/entrypoint.py` | Main CLI dispatcher |
| `src/reprostim/qr/qr_parse.py` | Video QR code extraction (JSONL output) |
| `src/reprostim/audio/audiocodes.py` | FSK/NFE audio codec generation |
| `src/reprostim/capture/nosignal.py` | No-signal frame detection algorithm |
| `.readthedocs.yaml` | Read the Docs build configuration |
| `.github/workflows/` | GitHub Actions CI/CD pipeline definitions |

## Configuration Files

| Config File | Role |
|-------------|------|
| `pyproject.toml` | Package metadata, dependencies, build backend (hatchling), tool configs |
| `CMakeLists.txt` | C++ build configuration, compiler flags, dependencies |
| `.readthedocs.yaml` | Read the Docs build environment, Python version |
| `.pre-commit-config.yaml` | Pre-commit hooks for code quality |
| `.codespellrc` | Spell checking configuration |
| `REUSE.toml` | SPDX license compliance configuration |
| `containers/*/Dockerfile*` | Container image definitions |
| `src/reprostim-capture/version.txt` | Version string for C++ build |

## Git Information

- **Current Branch**: `enh-perms` (enhancement for permissions)
- **Main Branch**: `master` (use for PRs)
- **Recent Commits**: Focus on permissions fixes, container generation, QR/nosignal features
- **License**: MIT
- **Version**: 0.7.x (Alpha development status)

## Team and Community

- **Organization**: ReproNim (Reproducible Neuroimaging)
- **Core Contributors**:
  - Yaroslav Halchenko (lead)
  - Vadim Melnik (active development)
  - Horea Christian
  - Andy Connolly
- **Project Links**:
  - GitHub: https://github.com/ReproNim/reprostim
  - Documentation: Read the Docs (configured)
  - PyPI: reprostim package

## Development Guidelines

### Code Quality
- Pre-commit hooks configured (see `.pre-commit-config.yaml`)
- Spell checking via codespell
- SPDX license compliance (REUSE.toml)
- Shellcheck for bash scripts (disable SC2086, SC2034 in build_reprostim.sh)

### Testing
- Run Python tests: `pytest tests/`
- Run C++ tests: `cd build && make test`
- CI tests: `tools/ci/test_reprostim_container.sh`

### Documentation
- Build docs: `cd docs && make html`
- Auto-generated CLI docs via sphinx-click
- Technical notes in `docs/source/notes/`

### Version Management
- Version source: Git tags
- Auto-generated: `src/reprostim/_version.py` via versioningit
- C++ version: `src/reprostim-capture/version.txt`

## Common Tasks

### Running CLI Commands
```bash
# Parse QR codes from video
reprostim qr-parse video.mkv

# Run PsychoPy time synchronization
reprostim timesync-stimuli

# Detect no-signal frames
reprostim detect-noscreen video.mkv

# Audit all videos
reprostim video-audit /path/to/videos

# Split/slice video to specific time range
reprostim split-video --start 2024-02-02T17:30:00 --duration P3M \
  --buffer-before 10 --buffer-after 10 \
  --input video.mkv --output sliced.mkv

# List displays
reprostim list-displays

# Monitor displays
reprostim monitor-displays
```

### Building Containers
```bash
cd containers/repronim-reprostim

# Generate templates
./generate_container.sh

# Build Docker (default mode - PyPI install)
./build_docker.sh

# Build for CI (install from worktree)
./build_docker.sh ci

# Build Singularity
./build_singularity.sh
```

### C++ Capture Tools
```bash
# After building and installing:
reprostim-videocapture -V          # Check version
reprostim-screencapture --help     # Screen capture help
```

## Notes and Caveats

1. **PsychoPy Version**: Container uses 2025.2.0 (latest) with Python 3.10
2. **Display Monitoring**: Platform-specific dependencies (pygame, pyglet, pyudev for Linux; quartz for macOS)
3. **Magewell SDK**: 3rdparty directory contains SDK versions 3.3.1.0 and 3.3.1.1313
4. **BIDS Integration**: Project designed to work within BIDS dataset structure
5. **Permissions**: Recent work on `/opt` permissions (enh-perms branch)
6. **Container Modes**: CI mode installs from worktree, default mode from PyPI

## Recent Development Focus (from CHANGELOG)

- Video audit tool creation
- PsychoPy integration improvements
- Container support (Docker/Singularity)
- Display monitoring capabilities
- Audio codec improvements (FSK/NFE)
- Permissions fixes in container builds
- QR code and nosignal detection enhancements
