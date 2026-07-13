# `bids/properties.py` Task List

Tracks implementation progress against [spec-bids-properties.md](spec-bids-properties.md).

**Status:** two APIs implemented. `bids_properties_from_audio_video_info` and
`bids_properties_from_ffprobe` are done and tested manually; no automated test file exists yet.

---

## Core Logic

- [x] `_set_prop(props: Dict[str, Any], key: BidsMediaProperty, value: Any) -> None` — internal
      helper, sets `props[key.value] = value`, skips `None`; factored out of the mapping function
      itself so `bids_properties_from_va_record` (future) can reuse it
- [x] `bids_properties_from_audio_video_info(audio: Optional[AudioInfo], video: Optional[VideoInfo], props: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
  - [x] Returns a plain `Dict[str, Any]` keyed by `BidsMediaProperty.value` (sidecar JSON key
        strings), not by the enum member
  - [x] `RecordingDuration` — `video.duration_sec` preferred over `audio.duration_sec` when both
        present and video's is set
  - [x] `AudioCodec`/`AudioSampleRate`/`AudioChannelCount`/`AudioBitDepth`/`AudioCodecRFC6381`
        mapped from `AudioInfo` fields
  - [x] `VideoCodec`/`VideoFrameRate`/`VideoCodecRFC6381`/`ImageWidth`/`ImageHeight`/
        `ImagePixelFormat`/`ImageBitDepth` mapped from `VideoInfo` fields
  - [x] `VideoFrameCount` intentionally left unpopulated (no source field in `VideoInfo`)
  - [x] `None`-valued source fields omitted from the result entirely
  - [x] `audio=None` / `video=None` / both `None` handled without error
  - [x] `props=None` (default) → fresh dict created and returned, unchanged behavior
  - [x] `props=<dict>` → populated in place and returned as the same object (`result is props`),
        letting callers accumulate from multiple `bids_properties_from_*` calls; overlapping
        keys are overwritten by the current call's non-`None` values (`dict.update()` semantics
        — priority is by call order, not a feature of `props` itself)
- [x] `bids_properties_from_ffprobe(path: str, props: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
  - [x] Calls `reprostim.qr.video_audit.get_audio_video_info_ffprobe(path)`, passes result (and
        `props`, unchanged) to `bids_properties_from_audio_video_info`
  - [x] Nonexistent/unreadable path → `{}` (or the passed-in `props`, untouched) — no exception,
        since `get_audio_video_info_ffprobe` returns default-constructed `AudioInfo`/`VideoInfo`
        rather than raising or returning `None`
  - [x] Manually verified against a real fixture
        (`tests/data/reprostim-videos/2024.06.04-13.51.24.278--2024.06.04-13.51.31.057.mkv`)
        and the shared-`props` accumulation pattern (independent dicts by default, same object
        mutated/returned when shared, call-order priority)
- [ ] `bids_properties_from_va_record(record: VaRecord) -> Dict[str, Any]` — not implemented
- [ ] `get_bids_properties(path: str, va_record: Optional[VaRecord] = None) -> Dict[str, Any]` —
      not implemented (single orchestrating entry point over `bids_properties_from_va_record`
      and `bids_properties_from_ffprobe`)
- [ ] Wire into `bids/inject_sidecar.py::_do_sidecar` (currently calls `parse_bids_media_info`
      only, not this module)
- [ ] Factor `split_video.py::_to_bids_model` to use this module (no behavior change)

---

## Documentation

- [x] `bids.properties` added to RTD API reference autosummary (`docs/source/api/index.rst`)
- [x] Cross-referenced from `.ai/context.md` `bids/` module list

---

## Tests and Code Coverage

Proposed test file location: `tests/bids/test_properties.py`. No automated tests exist yet —
manually verified during development (audio+video, audio-only, video-only, neither).

- [ ] `bids_properties_from_audio_video_info(audio, video)` — both present → all mappable fields
      present, `VideoFrameCount` absent
- [ ] `bids_properties_from_audio_video_info(audio, None)` — audio-only fields present, no
      video-derived keys, `RecordingDuration` from `audio.duration_sec`
- [ ] `bids_properties_from_audio_video_info(None, video)` — video-only fields present, no
      audio-derived keys, `RecordingDuration` from `video.duration_sec`
- [ ] `bids_properties_from_audio_video_info(None, None)` → `{}`
- [ ] A `None`-valued field on `AudioInfo`/`VideoInfo` (e.g. `codec=None`) is omitted from the
      result, not written as `None`/`"n/a"`
- [ ] Result keys are plain strings (`"AudioCodec"`, not `BidsMediaProperty.AUDIO_CODEC`)
- [ ] `_set_prop` — skips `None`, sets `props[key.value]` for a non-`None` value
- [ ] `bids_properties_from_ffprobe(path)` for a real audio+video fixture → matches
      `bids_properties_from_audio_video_info(*get_audio_video_info_ffprobe(path))`
- [ ] `bids_properties_from_ffprobe` for a nonexistent path → `{}`, no exception raised
- [ ] `props=None` (default, both functions) → returns a fresh dict each call (not the same
      object across calls)
- [ ] `props=<dict>` (both functions) → return value `is` the passed-in dict
- [ ] `props=<dict>` with a pre-existing unrelated key → that key survives untouched
- [ ] `props=<dict>` with a pre-existing key this call also sets → overwritten by this call's
      non-`None` value
- [ ] Two calls into the same shared `props` (e.g. audio-only then video-only) → both sets of
      keys present in the final dict

### Coverage targets

| Module | Target |
|---|---|
| `bids/properties.py` | ≥ 90% |

---

## Open Questions / Future Work

- [ ] `bids_properties_from_va_record` — field mapping from `VaRecord` columns; should accept the
      same optional `props` param for consistency with the other `bids_properties_from_*`
      functions
- [ ] `get_bids_properties` — orchestration entry point (path → va_record lookup →
      `bids_properties_from_ffprobe` fallback)
- [ ] `VideoFrameCount` source (add upstream field vs. approximate vs. leave unset)
- [ ] `RecordingDuration` precedence when `audio.duration_sec` and `video.duration_sec` disagree
- [ ] `reprostim.qr.video_audit` import path will need updating if/when `video_audit.py` moves
      out of `qr/` per the broader package reorganization
