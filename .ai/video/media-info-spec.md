# `video/media_info.py` Specification

## Overview

`reprostim.video.media_info` is a small, dependency-light API that extracts audio/video stream
information (codec, resolution, duration, sample rate, etc.) from a media file. It is currently
implemented on top of `ffprobe`, but the module is deliberately named and organized around the
*result* (media stream info), not the *mechanism* — callers should never need to know or care
that `ffprobe` is involved, so the extraction backend can change later without forcing an import
change at any call site.

### Why this module exists

The module was extracted out of `video/audit.py`, where this logic originally lived (see the
`# NB: move in future to audio package or tool?` comment that used to sit on `AudioInfo`). Two
things forced the move:

1. **Reuse without a mechanism leak.** `video/split.py` and `bids/properties.py` already imported
   `AudioInfo`/`VideoInfo`/`get_audio_video_info_ffprobe`/`parse_audio_sr` from `video/audit.py`,
   even though none of that logic is specific to audit orchestration.
2. **Avoiding a circular import.** `video/audit.py` imports from `qr/parse.py`
   (`do_parse`/`do_info_file`/etc.). Work on `qr-parse`'s `-S/--start-time` /
   `-E/--end-time` options (see the BIDS/QR timing work) needs a duration source for videos whose
   filenames don't follow the naming convention, and `get_audio_video_info_ffprobe` is exactly
   that source — but `qr/parse.py` importing it back from `video/audit.py` would be circular.
   Extracting it into `video/media_info.py` (no dependency on `qr/parse.py` or on `video/audit.py`)
   lets both sides depend on it safely.

---

## Public API

| Symbol | Kind | Description |
|--------|------|-------------|
| `AudioInfo` | Pydantic model | Audio stream fields: `codec`, `codec_long`, `codec_rfc6381`, `profile`, `sample_rate`, `channels`, `bits_per_sample`, `duration_sec`, `start_time`, `tag_str`. All fields `Optional`, `None` when not determined. |
| `VideoInfo` | Pydantic model | Video stream fields: `codec`, `codec_long`, `codec_rfc6381`, `profile`, `level`, `width`, `height`, `pix_fmt`, `bit_depth`, `fps`, `frame_count`, `duration_sec`, `start_time`, `tag_str`. All fields `Optional`, `None` when not determined. |
| `check_ffprobe() -> bool` | Function | Returns `True` if `ffprobe` is installed and runnable (`ffprobe -version` succeeds), `False` otherwise. |
| `get_audio_video_info_ffprobe(path: str, count_frames: bool = False) -> Tuple[AudioInfo, VideoInfo]` | Function | Runs a single `ffprobe -show_streams` call, splits the result into the first audio stream and first video stream found. `count_frames=True` passes `-count_frames` for an exact `nb_read_frames` count (full decode pass — slow); default `False` falls back to container `nb_frames` or an `fps * duration_sec` estimate. Never raises — on `ffprobe` missing or failing, logs an error and returns default-constructed (`None`-valued) `AudioInfo`/`VideoInfo`. |
| `parse_audio_sr(audio_sr: Optional[str]) -> dict` | Function | Parses a composite string like `'48000Hz 16b 2ch aac'` (the format `video/audit.py::do_audit_file` assembles for `VaRecord.audio_sr`) back into `audio_sample_rate`/`audio_bit_depth`/`audio_channel_count`/`audio_codec` string fields. Returns all-`"n/a"` on `None`/`"n/a"`/empty/unparseable input. |
| `audio_codec_to_rfc6381(codec: str, profile: Optional[str]) -> Optional[str]` | Function | Maps an `ffprobe` audio codec name + profile to an RFC 6381 codec string (e.g. `"aac"` + `"LC"` → `"mp4a.40.2"`). `None` for unrecognized codecs. |
| `video_codec_to_rfc6381(codec: str, profile: Optional[str], level: Optional[int]) -> Optional[str]` | Function | Maps an `ffprobe` video codec name + profile + level to an RFC 6381 codec string (e.g. `"h264"` + `"High"` + `42` → `"avc1.64002A"`). Only `h264` is currently mapped; `None` for anything else. |

---

## Consumers

- `video/audit.py` — `do_audit_file` calls `get_audio_video_info_ffprobe` for the `INTERNAL` audit
  source; `do_main` calls `check_ffprobe` as a startup precondition check.
- `video/split.py` — uses `parse_audio_sr` to recover typed audio fields from a `SplitDevice`'s
  composite audio-info string.
- `bids/properties.py` — `bids_properties_from_ffprobe`/`bids_properties_from_audio_video_info`
  consume `AudioInfo`/`VideoInfo` (via `get_audio_video_info_ffprobe`) to build BIDS sidecar
  properties.
- `qr/parse.py` — (planned) the `-S/--start-time auto` / `-E/--end-time auto` fallback path uses
  `get_audio_video_info_ffprobe`'s `VideoInfo.duration_sec` when a video's filename doesn't match
  the timestamped naming pattern, to compute the missing bound from the other one plus real
  duration. See `qr/parse-spec.md` (once updated) for that feature.

---

## Design notes

- **No dependency on `qr/parse.py` or `video/audit.py`.** This is the whole point of the module —
  it must stay a leaf dependency so both `video/audit.py` and `qr/parse.py` can import from it
  without introducing a cycle.
- **Function names still say "ffprobe".** `get_audio_video_info_ffprobe`'s own name references
  the mechanism even though the *module* doesn't. This is intentional for this extraction pass —
  renaming it would touch every call site (`audit.py`, `split.py`, `bids/properties.py`) for no
  behavioral gain. A mechanism-agnostic rename (e.g. `get_audio_video_info`) is a reasonable
  future follow-up if/when a second backend is actually added.
- **Test-mock target.** Callers that `from reprostim.video.media_info import X` and call `X(...)`
  directly (not via a module-qualified reference) get patched at `reprostim.video.audit.X`,
  `reprostim.bids.properties.X`, etc. — i.e. at the *importing* module's namespace, per normal
  Python import-binding semantics. Tests of `media_info.py`'s own logic patch
  `reprostim.video.media_info.subprocess.run` directly.
