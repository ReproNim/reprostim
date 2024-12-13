# ReproStim Python library/CLI

## Current status

This repository collects various sub-projects 

- Magewell SDK
- C++ code of ReproStim `reprostim-videocapture` (and `reprostim-screencapture`)
- ReproEvents for MicroPython board
- ReproStim videograbber
- ReproStim stimuli for calibration

## The Goal

Refactor stuff here into cleanly separated and documented libraries etc.

## Approach/Layout

- `src/`
  - `reprostim/` - Python library and CLIs for working with ReproStim
    - `audio/` - Audio fingerprinting/processing
    - `cli/` - CLI entrypoints (for `reprostim CMD`, could be hierarchical like `reprostim qr parse`)
      - `base.py` - common base commands for CLI
      - `cmd_timesync_stimuli.py` - CLI to replace `tools/reprostim-timesync-stimuli`
    - `qr/` - QR code utilities
    - `__init__.py` - sets up the library
  - `reprostim-capture/` - C++ code(s) relating to capturing
    - `lib/` - Magewell SDK
  - `reproevents/` - move MicroPython ReproEvents here (do not strive to make it work)
- `test/` - some global tests possibly for integration testing etc

## Refactor log

| Old       | New                     |
|-----------|-------------------------|
| `Capture` | `src/reprostim-capture` |
| `Events`  | `src/reproevents`       |