# `bids/properties.py` Task List

Tracks implementation progress against [spec-bids-properties.md](spec-bids-properties.md).

**Status:** three APIs implemented, all with automated tests in `tests/bids/test_properties.py`
(39 tests total — 17 for `bids_properties_from_split_result` moved from
`tests/qr/test_split_video.py`'s `_to_bids_model` tests, plus 15 new for
`bids_properties_from_audio_video_info`, 3 for `bids_properties_from_ffprobe`, and 4 exercising
previously-uncovered exception branches in `bids_properties_from_split_result`).
`src/reprostim/bids/properties.py` is at **100% statement coverage** (`--cov-report=term-missing`
shows no missing lines). Along the way, fixed a latent bug: `ImageBitDepth` from
`sidecar_metadata` was `int()`-converted with no `try/except`, unlike every sibling numeric
field — a malformed value (e.g. `"not-a-number"`) would have raised uncaught instead of being
omitted; now wrapped to match the others.

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

Test file: `tests/bids/test_properties.py` — **41 tests, 100% statement coverage of
`bids/properties.py`** (`pytest --cov=reprostim.bids.properties --cov-report=term-missing`).
17 tests for `bids_properties_from_split_result` were moved verbatim from
`tests/qr/test_split_video.py`'s `_to_bids_model` tests and renamed; 24 more were added to bring
`bids_properties_from_audio_video_info`/`bids_properties_from_ffprobe` from zero automated
coverage to full, and to close the remaining exception-branch gaps in
`bids_properties_from_split_result`.

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
- [x] `test_bids_properties_from_split_result_invalid_video_width_omitted` — non-numeric
      `video_width` omitted, not raised (exception-branch coverage)
- [x] `test_bids_properties_from_split_result_invalid_video_height_omitted`
- [x] `test_bids_properties_from_split_result_invalid_audio_sample_rate_omitted`
- [x] `test_bids_properties_from_split_result_invalid_audio_bit_depth_omitted`
- [x] `test_bids_properties_from_split_result_invalid_audio_channel_count_omitted`
- [x] `test_bids_properties_from_split_result_invalid_image_bit_depth_from_sidecar_omitted` —
      also the regression test for the `ImageBitDepth` bug fix (see Status above)
- [x] `test_bids_properties_from_split_result_invalid_video_frame_count_from_sidecar_omitted`
- [ ] No test covers `sr` being a non-`SplitResult` duck-typed object (only real `SplitResult`
      instances used) — the untyped-parameter contract itself isn't directly exercised

### `bids_properties_from_audio_video_info` / `bids_properties_from_ffprobe` (implemented)

- [x] `test_audio_video_info_both_present_full_mapping` — both present, all 14 fields incl.
      `VideoFrameCount` (exact-dict assertion, not just spot checks)
- [x] `test_audio_video_info_recording_duration_prefers_video_when_both_set`
- [x] `test_audio_video_info_recording_duration_falls_back_to_audio` —
      `video.duration_sec=None` falls back to `audio.duration_sec`
- [x] `test_audio_video_info_recording_duration_absent_when_neither_available`
- [x] `test_audio_video_info_audio_only` — audio-only fields present,
      `RecordingDuration` from `audio.duration_sec`
- [x] `test_audio_video_info_video_only` — video-only fields present incl.
      `VideoFrameCount`, `RecordingDuration` from `video.duration_sec`
- [x] `test_audio_video_info_both_none_returns_empty_dict`
- [x] `test_audio_video_info_none_valued_audio_field_omitted`
- [x] `test_audio_video_info_none_valued_video_field_omitted`
- [x] `_set_prop` — covered indirectly (it's the sole mechanism `bids_properties_from_audio_video_info`
      uses to populate every field; no direct unit test needed)
- [x] `test_ffprobe_calls_get_audio_video_info_and_maps` — mocks
      `reprostim.bids.properties.get_audio_video_info_ffprobe`, asserts result matches
      `bids_properties_from_audio_video_info` called with the same `(audio, video)`
- [x] `test_ffprobe_no_streams_returns_empty_dict` — mocked default-constructed
      `AudioInfo()`/`VideoInfo()` → `{}`, no exception (matches
      `get_audio_video_info_ffprobe`'s real never-raises contract)
- [x] `test_ffprobe_props_passthrough`
- [x] `test_audio_video_info_props_default_creates_fresh_dict_each_call`
- [x] `test_audio_video_info_props_shared_dict_mutated_and_returned`
- [x] `test_audio_video_info_props_overwrites_existing_key`
- [x] `test_audio_video_info_props_preserves_unrelated_key`
- [x] `test_audio_video_info_props_accumulates_across_two_calls` — audio-only then video-only
      into the same shared dict; both sets of keys present

### Coverage targets

| Module | Target | Actual |
|---|---|---|
| `bids/properties.py` | ≥ 90% | **100%** (statement) |

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
