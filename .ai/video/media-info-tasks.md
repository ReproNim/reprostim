# `video/media_info.py` Task List

Tracks implementation progress against [media-info-spec.md](media-info-spec.md).

---

## Extraction from `video/audit.py`

**Goal**: Move `ffprobe`-based stream-info extraction out of `video/audit.py` into a new,
mechanism-agnostic `video/media_info.py`, so `qr/parse.py` can depend on it too (for the
`-S/--start-time` / `-E/--end-time` `auto`-fallback duration source) without creating a circular
import (`video/audit.py` imports from `qr/parse.py`).

**Affected files**:
- `src/reprostim/video/media_info.py` (new)
- `src/reprostim/video/audit.py`
- `src/reprostim/video/split.py`
- `src/reprostim/bids/properties.py`
- `tests/video/test_media_info.py` (new)
- `tests/video/test_audit.py`
- `tests/bids/test_inject.py`
- `tests/bids/test_properties.py`

### Tasks

- [x] Create `video/media_info.py` with `AudioInfo`, `VideoInfo`, `check_ffprobe`,
  `parse_audio_sr`, `audio_codec_to_rfc6381`, `video_codec_to_rfc6381`,
  `get_audio_video_info_ffprobe` — moved verbatim from `video/audit.py`, no behavior change.
- [x] `video/audit.py`: remove the moved definitions; import `AudioInfo`, `check_ffprobe`,
  `get_audio_video_info_ffprobe` from `video/media_info.py` (only the symbols `audit.py` itself
  still uses — `VideoInfo`/`audio_codec_to_rfc6381`/`video_codec_to_rfc6381` were unused there
  once `get_audio_video_info_ffprobe` moved out).
- [x] `video/split.py`: import `parse_audio_sr` from `video/media_info.py` instead of
  `video/audit.py`.
- [x] `bids/properties.py`: import `AudioInfo`, `VideoInfo`, `get_audio_video_info_ffprobe`,
  `parse_audio_sr` from `video/media_info.py`; keep `VaRecord`/`get_file_video_audit` imported
  from `video/audit.py` (those did not move).
- [x] Move the corresponding unit tests (`parse_audio_sr`, `check_ffprobe`,
  `audio_codec_to_rfc6381`/`video_codec_to_rfc6381`, `get_audio_video_info_ffprobe` — 24 tests
  total) from `tests/video/test_audit.py` to new `tests/video/test_media_info.py`; update their
  `subprocess.run` patch targets from `reprostim.video.audit.subprocess.run` to
  `reprostim.video.media_info.subprocess.run`.
- [x] `tests/video/test_audit.py`: drop the now-moved symbols from its `video.audit` import block;
  add `from reprostim.video.media_info import VideoInfo` (still needed for
  `MagicMock(spec=VideoInfo)` in `test_do_audit_file_happy_path`). Integration-level tests that
  patch `reprostim.video.audit.check_ffprobe` / `reprostim.video.audit.get_audio_video_info_ffprobe`
  (testing `audit.py`'s own orchestration, not the extracted functions' logic) needed **no**
  changes — those patch targets still resolve correctly against `audit.py`'s re-import.
- [x] `tests/bids/test_inject.py`, `tests/bids/test_properties.py`: update
  `from reprostim.video.audit import AudioInfo, VideoInfo[, VaRecord]` to import
  `AudioInfo`/`VideoInfo` from `video/media_info.py` (their `reprostim.bids.properties.
  get_audio_video_info_ffprobe` patch targets were already correct and needed no changes, for the
  same re-import reason as above).
- [x] Full test suite green (`tests/video/`, `tests/bids/`, and repo-wide) after the move — no
  regressions, no leftover references to the old `video.audit.{AudioInfo,VideoInfo,check_ffprobe,
  get_audio_video_info_ffprobe,parse_audio_sr,audio_codec_to_rfc6381,video_codec_to_rfc6381}`
  paths anywhere in `src/` or `tests/`.
- [x] `.ai/context.md`: add a `media_info.py` bullet under the `video/` section; update the
  `nosignal.py` bullet's `VideoInfo` collision-avoidance note to point at `video/media_info.py`
  instead of `video/audit.py`.
- [x] `.ai/video/media-info-spec.md` / `.ai/video/media-info-tasks.md` (this file) created.

### Explicitly out of scope for this pass

- Renaming `get_audio_video_info_ffprobe` to drop the mechanism-specific `_ffprobe` suffix (would
  touch every call site for no behavior change — noted as a possible future follow-up in the spec).
- Any change to `qr/parse.py` itself — this extraction is a prerequisite for the `-S/--start-time`
  / `-E/--end-time` feature, tracked separately.
