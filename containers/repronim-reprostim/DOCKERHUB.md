# ReproStim Docker Container

[![Docker Pulls](https://img.shields.io/docker/pulls/repronim/reprostim.svg)](https://hub.docker.com/r/repronim/reprostim)
[![Docker Image Size](https://img.shields.io/docker/image-size/repronim/reprostim/latest.svg)](https://hub.docker.com/r/repronim/reprostim)
[![Read the Docs](https://app.readthedocs.org/projects/reprostim/badge/?version=latest)](https://reprostim.readthedocs.io/en/latest/)
[![Tests](https://github.com/ReproNim/reprostim/actions/workflows/pytest.yml/badge.svg)](https://github.com/ReproNim/reprostim/actions/workflows/pytest.yml)
[![PyPI Version](https://img.shields.io/pypi/v/reprostim.svg)](https://pypi.org/project/reprostim/)
[![GitHub release](https://img.shields.io/github/release/ReproNim/reprostim.svg)](https://GitHub.com/ReproNim/reprostim/releases/)
[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](https://raw.githubusercontent.com/ReproNim/reprostim/master/LICENSES/MIT.txt)

A reproducible environment for running the [ReproStim](https://github.com/ReproNim/reprostim) toolkit - tools for reproducible stimuli delivery and synchronization in neuroimaging experiments.

## Quick Start

Pull the latest image:

```bash
docker pull repronim/reprostim:latest
```

Pull a specific version:

```bash
docker pull repronim/reprostim:0.7.18
```

## Usage

### Check Version

```bash
docker run --rm repronim/reprostim:latest python3 -m reprostim --version
```

### Run Time Synchronization

```bash
docker run --rm \
  -v $(pwd):/data \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  repronim/reprostim:latest \
  python3 -m reprostim timesync-stimuli -t 10 --mode interval
```

### Interactive Shell

```bash
docker run -it --rm repronim/reprostim:latest bash
```

## Available Tags

- `latest` - Latest stable release
- `master` - Built from master branch
- `X.Y.Z` - Specific version tags (e.g., `0.7.5`)

## Documentation

- **Full Documentation**: https://reprostim.readthedocs.io
- **GitHub Repository**: https://github.com/ReproNim/reprostim
- **Issues & Support**: https://github.com/ReproNim/reprostim/issues

## Features

The ReproStim container includes:
- Audio and visual stimulus delivery tools
- Time synchronization utilities
- Support for video capture and monitoring
- Pre-configured PsychoPy environment

## Requirements

For audio/visual features, you may need to share additional host resources:
- X11 display for visual output
- PulseAudio for audio output
- Video devices for capture

## License

See the [LICENSE](https://github.com/ReproNim/reprostim/blob/master/LICENSE) file in the GitHub repository.