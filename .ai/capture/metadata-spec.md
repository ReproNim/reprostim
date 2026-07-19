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

### `MetadataType(str, Enum)`

The `"type"` field values reprostim-videocapture writes, mirrored from the
`_METADATA_LOG` call sites in
`src/reprostim-capture/videocapture/src/VideoCapture.cpp` (must be kept in
sync with that file — these are the only three values it currently emits):

| Member          | Value             | Emitted when...                                                                    |
|-----------------|-------------------|-------------------------------------------------------------------------------------|
| `SESSION_BEGIN` | `"session_begin"` | Recording session starts; carries device/session info (`serial`, `vDev`, `aDev`, `cx`, `cy`, `frameRate`, `autoRecovery`, `cap_ts_start`/`cap_isotime_start`) |
| `CAPTURE_STOP`  | `"capture_stop"`  | Capture stops (`message` explains why); carries `cap_ts_start`/`cap_isotime_start` and `cap_ts_stop`/`cap_isotime_stop` |
| `SESSION_END`   | `"session_end"`   | Session logger closes, after the ffmpeg thread has terminated; carries `message` and `cap_ts_start`/`cap_isotime_start` |

Not yet wired into any `find_metadata_json(..., "type", ...)` call site —
those still pass the raw string literal `"session_begin"` (see
`video/audit.py::do_audit_file`, `video/split.py::_split_video`,
`bids/properties.py::bids_properties_from_video_audit`). Left as-is for
now; switching them to `MetadataType.SESSION_BEGIN` is a follow-up, not
done as part of adding the enum.

### `MetadataBase`, `MetadataSessionBegin`, `MetadataCaptureStop`, `MetadataSessionEnd`

Pydantic models for the three `MetadataType` payload shapes, mirroring the
`_METADATA_LOG` call sites in `VideoCapture.cpp` field-for-field.

**All fields are `Optional[str] = None`, deliberately** — this is a
weakly-typed first pass mirroring the raw C++ JSON, not a semantically
typed model (no parsed timestamps, no numeric resolution). A shared
`field_validator("*", mode="before")` on `MetadataBase` stringifies every
field on load, so JSON types the C++ side actually writes as non-string —
`cx`/`cy` (numbers), `autoRecovery` (bool) — are coerced to `str` instead of
raising a validation error. Constructing directly from a `find_metadata_json`/
`iter_metadata_json` result (a plain `dict`) works via `MetadataSessionBegin(**msg)`.

`MetadataBase` fields (shared by all three, since every `_METADATA_LOG`
call site writes them): `type`, `version`, `json_ts`, `json_isotime`,
`cap_ts_start`, `cap_isotime_start`.

| Model                 | Type value        | Extra fields (beyond `MetadataBase`)                                             |
|-----------------------|-------------------|-----------------------------------------------------------------------------------|
| `MetadataSessionBegin` | `session_begin`   | `appName`, `serial`, `vDev`, `aDev`, `cx`, `cy`, `frameRate`, `autoRecovery`        |
| `MetadataCaptureStop`  | `capture_stop`    | `message`, `cap_ts_stop`, `cap_isotime_stop`                                       |
| `MetadataSessionEnd`   | `session_end`     | `message`                                                                          |

Neither `iter_metadata_json` nor `find_metadata_json` construct these models
— they still return raw `dict`s. `find_metadata_by_class` (below) is what
constructs them.

### `find_metadata_by_class(path: str, cls: Type[T]) -> Optional[T]`

Find the first metadata entry matching `cls`'s `MetadataType` and parse it
as `cls` — e.g. `find_metadata_by_class(path, MetadataSessionBegin)` returns
a `MetadataSessionBegin` (or `None`).

Internally: looks up `cls`'s corresponding `MetadataType` via the private
`_find_metadata_type_by_class(cls)` helper (a lookup against the
module-level `_METADATA_TYPE_BY_CLASS` dict — `MetadataSessionBegin` →
`MetadataType.SESSION_BEGIN`, etc. — kept separate from the model classes
themselves rather than a class attribute on `MetadataBase`), then calls
`find_metadata_json(path, "type", metadata_type.value)` and constructs
`cls(**msg)`.

If `cls` isn't one of the three known typed subclasses (e.g. `MetadataBase`
itself, or any custom subclass not in `_METADATA_TYPE_BY_CLASS`), there's no
`"type"` to search for — logs an error (`"No MetadataType found for
class: ..."`) and returns `None` rather than guessing or falling back to an
untyped result.

Wiring this into `video/audit.py`, `video/split.py`, `bids/properties.py`
(which still call `find_metadata_json(..., "type", "session_begin")`
directly and work with raw dicts) is a follow-up — see Open Questions.

---

## Log Format Reference

Real `reprostim-videocapture` log excerpt (see
`tests/data/capture/metadata-videocapture.mkv.log`):

```
2025-11-05 14:03:28.837 [INFO] [3774603] REPROSTIM-METADATA-JSON: {"aDev":"hw:3,0","appName":"reprostim-videocapture","autoRecovery":false,"cap_isotime_start":"2025-11-05T14:03:28.837026","cap_ts_start":"2025.11.05-14.03.28.837","cx":1920,"cy":1080,"frameRate":"60","json_isotime":"2025-11-05T14:03:28.837431","json_ts":"2025.11.05-14.03.28.837","serial":"TESTSERIAL0001","type":"session_begin","vDev":"USB Capture HDMI","version":"1.11.0.347"} :REPROSTIM-METADATA-JSON
```

A single log typically contains three such lines in sequence, one each for
`type: session_begin`, `type: capture_stop`, `type: session_end`, with
arbitrary non-matching log/ffmpeg output lines (including blank lines and
multi-line ffmpeg banners) interleaved between them.

---

## Open Questions / Future Work

- All `Metadata*` model fields are `str`/`Optional[str]` for now — no
  semantic typing (parsed `datetime` for `cap_isotime_start` etc., `int`
  for `cx`/`cy`, `bool` for `autoRecovery`). Deliberate first pass; a
  follow-up could add real types once callers actually need them.
- `MetadataType` isn't wired into the existing `find_metadata_json(...,
  "type", "session_begin")` call sites yet (see `MetadataType` section
  above) — they still use the raw string literal.
- `video/audit.py`, `video/split.py`, `bids/properties.py` still work with
  raw `dict`/`.get(key)` results from `find_metadata_json` — none of them
  use `find_metadata_by_class`/construct `MetadataSessionBegin`/etc. yet.
- `find_metadata_json` rescans the whole file on every call with no
  caching; fine for today's call sites (one lookup per video), would need
  revisiting if a caller starts looking up many keys from the same file.
