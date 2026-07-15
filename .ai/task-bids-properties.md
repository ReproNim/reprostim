# `bids/properties.py` Task List

Tracks implementation progress against [spec-bids-properties.md](spec-bids-properties.md).

**Status:** three APIs implemented, automated tests exist for `bids_properties_from_split_result`
(`tests/bids/test_properties.py`, 17 tests, moved from `tests/qr/test_split_video.py`'s
`_to_bids_model` tests). `bids_properties_from_audio_video_info`/`bids_properties_from_ffprobe`
are done and tested manually only — no automated test file for those two yet.

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
  - [x] `VideoFrameCount` mapped from `video.frame_count` (now populated upstream in
        `video_audit.py`)
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
- [x] Wire into `bids/inject.py::_call_split_video` — replaced its own direct
      `get_audio_video_info_ffprobe` call + manual `VideoCodecRFC6381`/`AudioCodecRFC6381`/
      `BitDepth`/`PixelFormat` selection with `bids_properties_from_ffprobe(input_path,
      props=sidecar_metadata)`; `sidecar_metadata` now also carries the other mappable
      properties (`AudioCodec`, `RecordingDuration`, etc.) that `bids_properties_from_split_result`
      doesn't currently read, harmlessly unused
- [ ] Wire into `bids/inject_sidecar.py::_do_sidecar` (currently calls `parse_bids_media_info`
      only, not this module)
- [x] `bids_properties_from_split_result(sr, sidecar_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`
      — **moved here from `split_video.py::_to_bids_model`** (not just naming-compatible
      anymore, actually the same code); `split_video.py::_write_sidecar` now imports and calls
      it. `split_video.py` no longer has any BIDS-mapping logic of its own.
  - [x] First parameter `sr` is intentionally **untyped** (no `SplitResult` annotation) — avoids
        `properties.py` importing from `qr/split_video.py`, which would be circular since
        `split_video.py` imports `bids_properties_from_split_result` from here
  - [x] `TaskName`/`Device`/`DeviceSerialNumber`/`RecordingDuration`/`VideoCodec`/
        `VideoCodecRFC6381`/`VideoFrameRate`/`ImageWidth`/`ImageHeight`/`ImageBitDepth`/
        `ImagePixelFormat`/`VideoFrameCount`/`AudioCodec`/`AudioCodecRFC6381`/
        `AudioSampleRate`/`AudioBitDepth`/`AudioChannelCount` all mapped (see
        [spec-split-video.md](spec-split-video.md) for the full source → field table)
  - [x] Does **not** currently accept a `props` accumulation parameter, unlike the other two
        functions in this module (open question below)
  - [x] `src/reprostim/qr/split_video.py` imports it from `reprostim.bids.properties`; the
        now-unused `from reprostim.bids.media import BidsMediaProperty` import was removed from
        `split_video.py` (moved with the function)

---

## Documentation

- [x] `bids.properties` added to RTD API reference autosummary (`docs/source/api/index.rst`)
- [x] Cross-referenced from `.ai/context.md` `bids/` module list

---

## Tests and Code Coverage

Test file: `tests/bids/test_properties.py` (exists — 17 tests for
`bids_properties_from_split_result`, moved verbatim from `tests/qr/test_split_video.py`'s
`_to_bids_model` tests and renamed; see checklist below). `bids_properties_from_audio_video_info`/
`bids_properties_from_ffprobe` still have **no automated tests** — manually verified during
development only (audio+video, audio-only, video-only, neither).

### `bids_properties_from_split_result` (implemented, in `tests/bids/test_properties.py`)

- [x] `test_bids_properties_from_split_result_full_mapping` — all populated `SplitResult` fields
      map to correct BIDS keys
- [x] `test_bids_properties_from_split_result_na_fields_omitted` — `"n/a"`-valued fields omitted
- [x] `test_bids_properties_from_split_result_none_values_omitted` — `None`-valued fields omitted
- [x] `test_bids_properties_from_split_result_numeric_types` — `ImageWidth`/`ImageHeight` as int,
      `AudioSampleRate` as float, `AudioChannelCount` as int
- [x] `test_bids_properties_from_split_result_video_codec_present_when_resolution_known`
- [x] `test_bids_properties_from_split_result_video_codec_absent_when_na`
- [x] `test_bids_properties_from_split_result_rfc6381_from_sidecar_metadata`
- [x] `test_bids_properties_from_split_result_rfc6381_defaults_to_na_without_sidecar_metadata`
- [x] `test_bids_properties_from_split_result_bit_depth_and_pixel_format_from_sidecar_metadata`
- [x] `test_bids_properties_from_split_result_bit_depth_and_pixel_format_absent_when_not_in_sidecar`
- [x] `test_bids_properties_from_split_result_video_frame_count_from_sidecar_metadata`
- [x] `test_bids_properties_from_split_result_video_frame_count_absent_when_not_in_sidecar`
- [x] `test_bids_properties_from_split_result_no_raw_fields` — no raw `SplitResult` field names
      leak into BIDS output
- [x] `test_bids_properties_from_split_result_task_name_first_field`
- [x] `test_bids_properties_from_split_result_task_name_absent_when_not_in_metadata`
- [x] `test_bids_properties_from_split_result_task_name_absent_when_metadata_is_none`
- [x] `test_bids_properties_from_split_result_task_name_first_before_device`
- [ ] No test covers `sr` being a non-`SplitResult` duck-typed object (only real `SplitResult`
      instances used) — the untyped-parameter contract itself isn't directly exercised

### `bids_properties_from_audio_video_info` / `bids_properties_from_ffprobe` (not yet automated)

- [ ] `bids_properties_from_audio_video_info(audio, video)` — both present, `video.frame_count`
      set → all mappable fields present including `VideoFrameCount`
- [ ] `bids_properties_from_audio_video_info(audio, video)` — `video.frame_count=None` →
      `VideoFrameCount` absent from the result
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
- [x] `VideoFrameCount` source — resolved: `VideoInfo.frame_count` added to `video_audit.py`
- [ ] `bids_properties_from_ffprobe` doesn't expose `count_frames` (from
      `get_audio_video_info_ffprobe`'s new param) — callers can't request the exact/slower
      frame count through this entry point yet
- [ ] `RecordingDuration` precedence when `audio.duration_sec` and `video.duration_sec` disagree
- [ ] `reprostim.qr.video_audit` import path will need updating if/when `video_audit.py` moves
      out of `qr/` per the broader package reorganization
- [ ] `bids_properties_from_split_result` doesn't accept a `props` accumulation parameter — add
      for consistency with the other two `bids_properties_from_*` functions, or confirm not
      needed
- [ ] Automated tests for `bids_properties_from_audio_video_info`/`bids_properties_from_ffprobe`
      — still manual-only, unlike `bids_properties_from_split_result`
