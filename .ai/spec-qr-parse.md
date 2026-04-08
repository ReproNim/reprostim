# QR Parse Tool Specification

## Overview

`qr-parse` (exposed via `reprostim parse-qr`) processes recorded video files to detect and extract
QR code data embedded in the video frames. It outputs timing and payload information for each QR
code found, enabling downstream tools to correlate stimulus events with video timestamps.

The core loop reads frames from an MKV/video file using OpenCV (`cv2.VideoCapture`), converts each
frame to grayscale, and attempts QR code detection via `pyzbar`. Detected codes are deduplicated
(consecutive frames showing the same QR are collapsed into a single record) and written to a
structured log/output.

---

## Optimization & Profiling

### Test video

All benchmarks were run against:

```
Videos/2025/08/2025.08.14-15.04.15.714--2025.08.14-16.00.26.656.mkv
```

- Resolution: 1280×800
- Frame rate: 60 fps

### Baseline measurements (2026-04-08)

All numbers are **frames per second (fps)** processed by the main frame loop in `qr_parse.py`.

| # | Configuration                                      | fps     | Notes                              |
|---|----------------------------------------------------|---------|------------------------------------|
| 1 | Empty loop — frames read, no grayscale, no decode  | 475.5   | I/O + `cap.read()` ceiling         |
| 2 | `np.mean(frame, axis=2)` only (no decode)          |  34.2   | Current code path                  |
| 3 | `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)` only     | 329.7   | ~10× faster than `np.mean`         |
| 4 | `cv2.cvtColor` + `pyzbar.decode`                   |  46.1   | Full pipeline, fast grayscale      |
| 5 | `np.mean` + `pyzbar.decode`                        |  23.7   | Full pipeline, current code        |

### Key takeaways

- **`np.mean` for grayscale is the biggest non-decode bottleneck.** It runs at 34.2 fps vs.
  329.7 fps for `cv2.cvtColor` — nearly a 10× difference for the same result.
- **`pyzbar.decode` dominates end-to-end cost** regardless of grayscale method, but switching
  grayscale conversion still doubles overall throughput (23.7 → 46.1 fps).
- **I/O ceiling** (`cap.read()` alone) is ~475 fps, so there is headroom for further optimization
  if decode cost can be reduced (e.g., skipping uniform frames, subsampling, or early-exit on
  low-contrast frames).
