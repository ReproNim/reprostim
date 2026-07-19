# Capture Metadata Specification

## Overview

`reprostim.capture.metadata` provides the shared API for extracting
`REPROSTIM-METADATA-JSON` entries embedded in `reprostim-videocapture` log
files (the `.log` sidecar written alongside each recorded `.mkv`). These
entries are single-line JSON blobs wrapped in `REPROSTIM-METADATA-JSON: ... :REPROSTIM-METADATA-JSON`
markers, interleaved with regular `ffmpeg`/capture log output, and record
capture lifecycle events such as `session_begin`, `capture_stop`, and
`session_end` (device name/serial, resolution, frame rate, start/stop
timestamps, etc.).

This module was factored out of `video/audit.py` (see
[../video/audit-spec.md](../video/audit-spec.md)) since the API doesn't
analyze recorded video at all — it only parses the capture-tool's own log
format — and is consumed by three otherwise-unrelated call sites:
`video/audit.py::do_audit_file` (session metadata for a `VaRecord`),
`video/split.py::_do_main_specs` (device name/serial for a split segment's
sidecar), and `bids/properties.py::bids_properties_from_video_audit`
(`Device`/`DeviceSerialNumber` BIDS fields). Grouping it under `capture/`
alongside `disp_mon.py` and `nosignal.py` — instead of leaving it in
`video/` or duplicating it across callers — reflects that it's capture-tool
metadata, not video-file analysis.

---

## API

### `JSON_PATTERN`

Module-level compiled regex: `REPROSTIM-METADATA-JSON: (.*) :REPROSTIM-METADATA-JSON`.
Captures the JSON payload between the two markers; used internally by
`iter_metadata_json`.

### `iter_metadata_json(log_path: str) -> Generator[Dict, None, None]`

Iterate over all `REPROSTIM-METADATA-JSON` lines in a log file, yielding
each payload parsed as a `dict`.

- Reads the file line-by-line (not loaded fully into memory), matching
  `JSON_PATTERN` against each line.
- Lines that don't match the marker pattern (ffmpeg output, other log
  lines) are silently skipped.
- A line that matches the marker but contains invalid JSON is logged
  (`logger.error`) and skipped — the generator does not raise.
- If `log_path` doesn't exist, logs an error and yields nothing (empty
  generator, not an exception) — callers don't need to check existence
  first.

### `find_metadata_json(path: str, key: str, value) -> Optional[Dict]`

Return the first entry from `iter_metadata_json(path)` whose `msg.get(key)
== value`, or `None` if no entry matches (including when the file is
missing or has no metadata lines at all). Thin `next(..., None)` wrapper
around `iter_metadata_json` — does not build an index; every call rescans
the file from the start.

Typical usage: `find_metadata_json(video_path + ".log", "type", "session_begin")`
to recover the capture device/session info for a given recorded video.

---

## Log Format Reference

Real `reprostim-videocapture` log excerpt (see
`tests/data/capture/metadata-videocapture.mkv.log`):

```
2025-11-05 14:03:28.837 [INFO] [3774603] REPROSTIM-METADATA-JSON: {"aDev":"hw:3,0","appName":"reprostim-videocapture","autoRecovery":false,"cap_isotime_start":"2025-11-05T14:03:28.837026","cap_ts_start":"2025.11.05-14.03.28.837","cx":1920,"cy":1080,"frameRate":"60","json_isotime":"2025-11-05T14:03:28.837431","json_ts":"2025.11.05-14.03.28.837","serial":"D206191219786","type":"session_begin","vDev":"USB Capture HDMI","version":"1.11.0.347"} :REPROSTIM-METADATA-JSON
```

A single log typically contains three such lines in sequence, one each for
`type: session_begin`, `type: capture_stop`, `type: session_end`, with
arbitrary non-matching log/ffmpeg output lines (including blank lines and
multi-line ffmpeg banners) interleaved between them.

---

## Open Questions / Future Work

- No typed data model exists yet for the parsed metadata dict — callers
  currently work with raw `dict`/`.get(key)` access. The original
  in-`video/audit.py` version of this code carried a note proposing typed
  data classes for parsed `reprostim-videocapture` metadata (e.g. a
  `SessionBeginInfo`/`CaptureStopInfo` pydantic model per `type`); not yet
  implemented.
- `find_metadata_json` rescans the whole file on every call with no
  caching; fine for today's call sites (one lookup per video), would need
  revisiting if a caller starts looking up many keys from the same file.
