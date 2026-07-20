# BIDS Media-File Properties Extraction Specification

## Overview

`properties.py` (`src/reprostim/bids/properties.py`) is the **single place** in the codebase that
produces BIDS media-file sidecar properties (the `BidsMediaProperty` keys defined in
[media-spec.md](media-spec.md)) — from `ffprobe`-derived `AudioInfo`/`VideoInfo` (via
`bids_properties_from_audio_video_info`, or directly from a file path via
`bids_properties_from_ffprobe`), from a `split-video` result (via
`bids_properties_from_split_result`), and from a cached `VaRecord` row (`videos.tsv`, via
`bids_properties_from_video_audit`).

This realizes what [inject-sidecar-spec.md § Relationship to `bids-inject` /
`split-video`](inject-sidecar-spec.md#relationship-to-bids-inject--split-video) originally
proposed: one module all consumers share, instead of each reimplementing the
`AudioInfo`/`VideoInfo`/`SplitResult`/`VaRecord` → BIDS-dict mapping independently.

**Status: four APIs implemented, two consumers wired up.** `bids_properties_from_audio_video_info`,
`bids_properties_from_ffprobe`, `bids_properties_from_split_result`, and
`bids_properties_from_video_audit` are done, all with 100% test coverage
(`tests/bids/test_properties.py`). `bids/inject.py::_call_split_video` calls
`bids_properties_from_ffprobe` to populate `sidecar_metadata`; `split_video.py::_write_sidecar`
calls `bids_properties_from_split_result` (moved here from `split_video.py::_to_bids_model`, which
no longer exists). `bids-inject-sidecar` (`_do_sidecar`) calls `bids_properties_from_ffprobe` but
**not yet** `bids_properties_from_video_audit` — the `--videos` cache-lookup path described in
[inject-sidecar-spec.md](inject-sidecar-spec.md) still needs to be wired up to call it
(see that spec's Open Questions). A cache-aware/path-orchestrating wrapper covering all sources
(preferring `VaRecord` when available, falling back to `ffprobe`) is future work (see Open
Questions).

---

## Motivation

`bids/media.py` deliberately stays close to the BEP044 spec — it's the taxonomy (enums,
`BidsMediaInfo`), not extraction logic (see [media-spec.md §
Overview](media-spec.md#overview)). Something still has to turn actual `ffprobe`/`split-video`
output into `BidsMediaProperty`-keyed values, though, and that logic needs one home so
`bids-inject-sidecar`, `bids-inject`, and `split-video` don't maintain separate,
potentially-drifting copies of the same field mapping. `properties.py` is that home —
`split_video.py::_to_bids_model` was moved here as `bids_properties_from_split_result` for
exactly this reason.

---

## Layering

`properties.py` depends on `bids/media.py` (for `BidsMediaProperty`) and on
`reprostim.video.audit` (for `AudioInfo`/`VideoInfo`, `VaRecord`, `get_audio_video_info_ffprobe`,
`get_file_video_audit`, `parse_audio_sr`) — not the reverse.
`bids/inject_sidecar.py`/`bids/inject.py`/`video/split.py` are expected to depend on
`properties.py` rather than reaching into `video.audit` directly or reimplementing the
mapping. **`bids/inject.py` and `video/split.py` both do this already**
(`_call_split_video` imports `bids_properties_from_ffprobe`, not `get_audio_video_info_ffprobe`;
`_write_sidecar` imports `bids_properties_from_split_result`); `video/split.py` separately
imports `parse_audio_sr` directly from `video.audit` (not via `properties.py`) in `_split_video`,
to populate `SplitResult`'s own `audio_sample_rate`/`audio_bit_depth`/`audio_channel_count`/
`audio_codec` fields from a `SplitDevice.audio_sr` string — that use is *not* mediated by
`properties.py`, since it produces `SplitResult` fields, not a BIDS properties dict.
`bids/inject_sidecar.py` still imports `parse_bids_media_info` from `bids/media.py` only, not
`bids_properties_from_video_audit` from `properties.py`.

> **`parse_audio_sr`** (`reprostim.video.audit.parse_audio_sr`) parses the composite
> `'48000Hz 16b 2ch aac'`-style string used by both `VaRecord.audio_sr` and `SplitDevice.audio_sr`
> into typed-ish string fields (`audio_sample_rate`/`audio_bit_depth`/`audio_channel_count`/
> `audio_codec`, `"n/a"` when absent). It lives in `video_audit.py` (not `properties.py`) since
> that's where the composite string format originates (`do_audit_file` assembles
> `VaRecord.audio_sr` from `AudioInfo`) and where `video/split.py` already depended on it before
> this session (as the now-removed `split_video._parse_audio_info`) — moving it to `properties.py`
> would have made `video/split.py`'s existing, unrelated use of it depend on `bids/properties.py`
> for no reason. `bids_properties_from_video_audit` (below) is the only place in `properties.py`
> that calls it.

`video/split.py` importing from `bids/properties.py` — `qr/` depending on `bids/` — mirrors
the same direction already established for `bids/media.py` (`BidsMediaProperty` is a leaf
taxonomy module anything can depend on); see the broader package-reorganization discussion this
session.

> **Circularity constraint**: `bids_properties_from_split_result`'s first parameter (`sr`) is
> deliberately **untyped**, not annotated `reprostim.video.split.SplitResult`. Since
> `split_video.py` calls into `properties.py`, having `properties.py` import `SplitResult` back
> from `split_video.py` would be circular. `sr` is documented as duck-typed instead — any object
> exposing the same attribute names as `SplitResult` works.

> `AudioInfo`/`VideoInfo`/`VaRecord` currently live in `reprostim/video/audit.py`, not yet
> moved to a `reprostim.media` package (see the broader package-reorganization discussion this
> session). `properties.py` importing from `reprostim.video.audit` reflects today's layout;
> only that one import line needs updating if/when `video_audit.py` moves.

---

## `bids_properties_from_audio_video_info` (implemented)

```python
def bids_properties_from_audio_video_info(
    audio: Optional[AudioInfo],
    video: Optional[VideoInfo],
    props: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]: ...
```

Maps `ffprobe`-derived `AudioInfo`/`VideoInfo` (from
`reprostim.video.audit.get_audio_video_info_ffprobe`) to a **plain `Dict[str, Any]`** keyed by
the exact BIDS sidecar JSON key (`BidsMediaProperty.value`, e.g. `"AudioCodec"`) — not by the
enum member itself, so the result can be merged/serialized directly without an extra
`.value` step at every call site.

### Shared `props` accumulation

Every `bids_properties_from_*` function in this module accepts an optional `props:
Optional[Dict[str, Any]] = None`. When omitted (the default), a fresh dict is created and
returned, matching the original no-argument behavior. When a dict is passed in, it is populated
**in place** (mutated) and returned as-is (`result is props`) — letting a caller accumulate
properties from several sources into one shared dict, e.g. the eventual `get_bids_properties`
orchestrator calling both `bids_properties_from_va_record(record, props=shared)` and
`bids_properties_from_ffprobe(path, props=shared)`.

**Priority between composed sources is controlled by call order, not by `props` itself**:
`_set_prop` overwrites a key unconditionally whenever the new value isn't `None` — plain
`dict.update()` semantics, last call wins. There is no separate "don't overwrite existing keys"
mode; if `--videos`-cache values should take priority over freshly-probed `ffprobe` values (per
[inject-sidecar-spec.md](inject-sidecar-spec.md)'s extraction priority order), the
caller achieves that by calling the higher-priority source's function *second*.

### Field mapping

| `BidsMediaProperty` | Source                                        |
|-----------------------|--------------------------------------------------|
| `RECORDING_DURATION`  | `video.duration_sec` if `video` given and set, else `audio.duration_sec` |
| `AUDIO_CODEC`         | `audio.codec`                                     |
| `AUDIO_SAMPLE_RATE`   | `audio.sample_rate`                               |
| `AUDIO_CHANNEL_COUNT` | `audio.channels`                                  |
| `AUDIO_BIT_DEPTH`     | `audio.bits_per_sample`                           |
| `AUDIO_CODEC_RFC6381` | `audio.codec_rfc6381`                             |
| `VIDEO_CODEC`         | `video.codec`                                     |
| `VIDEO_FRAME_RATE`    | `video.fps`                                       |
| `VIDEO_CODEC_RFC6381` | `video.codec_rfc6381`                             |
| `IMAGE_WIDTH`         | `video.width`                                     |
| `IMAGE_HEIGHT`        | `video.height`                                    |
| `IMAGE_PIXEL_FORMAT`  | `video.pix_fmt`                                   |
| `IMAGE_BIT_DEPTH`     | `video.bit_depth`                                 |
| `VIDEO_FRAME_COUNT`   | `video.frame_count` — exact `nb_read_frames` when `get_audio_video_info_ffprobe(path, count_frames=True)` was used, else `nb_frames` (container metadata) or an `fps * duration_sec` estimate (see `video_audit.py`) |

Any source field that is `None` is omitted from the result entirely (never written as `"n/a"` or
`None`), matching the BEP044 sidecar convention documented in
[media-spec.md](media-spec.md).

### `_set_prop` (internal helper)

```python
def _set_prop(props: Dict[str, Any], key: BidsMediaProperty, value: Any) -> None: ...
```

Sets `props[key.value] = value`, skipping `None`. Factored out (not a closure inside
`bids_properties_from_audio_video_info`) so `bids_properties_from_video_audit` below can reuse
it too.

---

## `bids_properties_from_ffprobe` (implemented)

```python
def bids_properties_from_ffprobe(
    path: str, props: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]: ...
```

Convenience wrapper: calls `reprostim.video.audit.get_audio_video_info_ffprobe(path)` to get
`(AudioInfo, VideoInfo)`, then passes them (plus `props`, unchanged) straight through to
`bids_properties_from_audio_video_info` — see [Shared `props`
accumulation](#shared-props-accumulation) above.
This is the direct-from-`ffprobe` counterpart to `bids_properties_from_video_audit` (cache-based)
below — together they back the still-TBD single orchestrating entry point (see Open Questions).

`get_audio_video_info_ffprobe` never returns `None` for either stream — it returns a
default-constructed (all-`None`-fields) `AudioInfo`/`VideoInfo` when a stream is absent or
`ffprobe` fails — so `bids_properties_from_ffprobe` on a nonexistent/unreadable path returns `{}`
rather than raising.

---

## `bids_properties_from_split_result` (implemented)

```python
def bids_properties_from_split_result(
    sr, sidecar_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]: ...
```

Moved here from `split_video.py::_to_bids_model` (same name pattern as this module's other
`bids_properties_from_*` functions). Converts a `split-video` result to a BEP044/BEP047 BIDS
sidecar dict — the function `split_video.py::_write_sidecar` calls for `SidecarFormat.BIDS`
output.

- **`sr` is untyped** (no `SplitResult` annotation) — see the Layering section's circularity
  note above. It's expected to expose `SplitResult`'s attributes: `orig_device`,
  `orig_device_serial_number`, `buffer_duration`, `video_codec`, `video_frame_rate`,
  `video_width`, `video_height`, `audio_codec`, `audio_sample_rate`, `audio_bit_depth`,
  `audio_channel_count`.
- **`sidecar_metadata`** (optional dict) supplies fields `sr` itself doesn't carry: `TaskName`
  (written first, when present), `VideoCodecRFC6381`, `AudioCodecRFC6381`, `ImageBitDepth`,
  `ImagePixelFormat`, `VideoFrameCount`. `bids/inject.py::_call_split_video` populates this dict
  via `bids_properties_from_ffprobe`, so in practice a single `ffprobe` call's result flows
  through as `sidecar_metadata` here.
- Unlike the other two functions in this module, `bids_properties_from_split_result` does **not**
  currently accept a `props` accumulation parameter (see [Shared `props`
  accumulation](#shared-props-accumulation) above) — it always builds and returns a fresh dict.
  Adding one for consistency is an open question below.
- Field mapping: see [video/split-spec.md § BIDS Sidecar
  Format](../video/split-spec.md#bids-sidecar-format---sidecar-format-implemented) for the full
  source → BIDS-field table (kept there since it documents `SplitResult`'s own field semantics,
  which this function's docstring can't reference directly due to the circularity constraint
  above).

---

## `bids_properties_from_video_audit` (implemented)

```python
def bids_properties_from_video_audit(
    path: str,
    path_tsv: Optional[str] = None,
    props: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]: ...
```

Looks up a cached `VaRecord` for *path* in *path_tsv* (a `videos.tsv` produced by `video-audit`)
and maps it to BIDS media-file properties — the cache-based counterpart to
`bids_properties_from_ffprobe` (direct-from-`ffprobe`) above.

- Calls `get_file_video_audit(path, path_tsv, cached=True, use_lock=False)` — always with
  `cached=True` (prefer already-loaded, in-process TSV data over reloading from disk) and
  `use_lock=False` (skip the advisory file lock, dirty-read mode). This is a deliberate choice
  for read-mostly batch tooling like `bids-inject-sidecar` reading a `videos.tsv` that
  `video-audit` itself is not concurrently writing — not appropriate for `video-audit`'s own
  writer path, which needs the lock. `get_file_video_audit` itself falls back to auditing the
  file directly (full `ffprobe`/QR-parse pass) when *path* has no matching row in *path_tsv*, or
  *path_tsv* isn't given/found.
- **Field mapping** uses the `VaRecord`'s `duration`/`video_res_recorded`/`video_fps_recorded`/
  `audio_sr` fields — not the `video_res_detected`/`video_fps_detected` ones. The `_recorded`
  fields are derived from the actual media stream (ffprobe/QR parsing, populated in
  `do_audit_file` from a `ParseSummary`), while the `_detected` fields are derived from the
  psychopy display-capture session log (what was *displayed*, not what's encoded in the file) —
  the sidecar should describe the file itself, so `_recorded` is the correct source.

  | `BidsMediaProperty`     | Source                                                          |
  |--------------------------|------------------------------------------------------------------|
  | `RECORDING_DURATION`    | `float(va.duration)`                                              |
  | `IMAGE_WIDTH`/`IMAGE_HEIGHT` | `va.video_res_recorded` (`"WxH"` string, split on `"x"`)     |
  | `VIDEO_FRAME_RATE`      | `float(va.video_fps_recorded)`                                    |
  | `AUDIO_SAMPLE_RATE`/`AUDIO_BIT_DEPTH`/`AUDIO_CHANNEL_COUNT`/`AUDIO_CODEC` | `parse_audio_sr(va.audio_sr)` |

  Any field that is `"n/a"` in the `VaRecord`, or fails to parse (non-numeric `duration`/
  `video_res_recorded`/`video_fps_recorded`/`audio_sample_rate` — `parse_audio_sr` doesn't
  digit-validate the `Hz` token), is omitted, matching every other `bids_properties_from_*`
  function in this module. `audio_bit_depth`/`audio_channel_count` from `parse_audio_sr` are
  never non-numeric other than `"n/a"` (that function's own `isdigit()` checks guarantee it), so
  those two conversions are **not** wrapped in `try/except` — unlike `RecordingDuration`/
  `ImageWidth`/`ImageHeight`/`VideoFrameRate`/`AudioSampleRate`, which are.
- No image (`ImagePixelFormat`/`ImageBitDepth`) or codec-RFC6381 fields — `VaRecord` doesn't carry
  them at all (see its field list in `video/audit.py`).
- Accepts the standard `props` accumulation parameter (see [Shared `props`
  accumulation](#shared-props-accumulation) above), unlike `bids_properties_from_split_result`.
- **Not yet wired up** to any consumer — `bids-inject-sidecar`'s `--videos` cache-lookup path
  (`ctx.videos_tsv`) is accepted but not consulted at all yet; see
  [inject-sidecar-spec.md](inject-sidecar-spec.md) Open Questions.

### `parse_audio_sr` (implemented, lives in `video/audit.py`)

```python
def parse_audio_sr(audio_sr: Optional[str]) -> dict: ...
```

Parses a composite `'48000Hz 16b 2ch aac'`-style string (the format `do_audit_file` assembles for
`VaRecord.audio_sr` from `AudioInfo`, and that `SplitDevice.audio_sr` also uses) into
`{"audio_sample_rate", "audio_bit_depth", "audio_channel_count", "audio_codec"}`, all strings,
`"n/a"` when a field can't be determined. Defaults `audio_bit_depth` to `"16"` when not present in
the string (a pre-existing quirk carried over unchanged from its previous home).

Moved from `video/split.py::_parse_audio_info` (private) to `video/audit.py::parse_audio_sr`
(public) this session, since `video_audit.py` is where the string format originates and where
both `video/split.py` (building `SplitResult` fields) and `bids/properties.py` (building BIDS
properties, via `bids_properties_from_video_audit`) need to consume it — a single shared
implementation instead of `properties.py` reimplementing the same parsing rules locally (which
would also have meant either duplicating the logic or `properties.py` importing from
`video/split.py`, circular per the Layering section above). Tests moved from
`tests/qr/test_split_video.py` to `tests/video/test_audit.py` accordingly.

---

## Open Questions / TODOs

- [x] `bids_properties_from_video_audit(path, path_tsv=None) -> Dict[str, Any]` — **resolved**:
      implemented, wraps `get_file_video_audit(path, path_tsv, cached=True, use_lock=False)`, maps
      the `_recorded`/`audio_sr`/`duration` `VaRecord` fields (see above). Not yet consumed by
      `bids-inject-sidecar`'s `--videos` option, though — that wiring remains open (see
      [inject-sidecar-spec.md](inject-sidecar-spec.md)).
- [ ] `get_bids_properties(path: str, path_tsv: Optional[str] = None) -> Dict[str, Any]` —
      single orchestrating entry point: resolve `path_tsv` → `bids_properties_from_video_audit`,
      else `bids_properties_from_ffprobe(path)`. This is what `bids-inject-sidecar`'s
      `_do_sidecar` should eventually call instead of invoking `parse_bids_media_info`/`ffprobe`
      itself.
- [x] `VIDEO_FRAME_COUNT` — resolved: `VideoInfo.frame_count` added upstream in `video_audit.py`
      (exact `nb_read_frames` via new `get_audio_video_info_ffprobe(path, count_frames=True)`
      param, else `nb_frames`, else `fps × duration_sec` estimate corrected for stream start
      offset), and wired into `bids_properties_from_audio_video_info`.
- [ ] `bids_properties_from_ffprobe` doesn't expose `count_frames` — always calls
      `get_audio_video_info_ffprobe(path)` (default `count_frames=False`), so callers can't
      request the exact (slower, full-decode) frame count through this entry point yet.
- [ ] `RecordingDuration` precedence when both `audio.duration_sec` and `video.duration_sec` are
      present but differ (currently: video wins unconditionally) — confirm this is the right
      default, or whether a mismatch should itself be surfaced somehow.
- [x] Wire `bids_properties_from_ffprobe` into `bids/inject.py::_call_split_video` (replacing its
      own direct `get_audio_video_info_ffprobe` call + manual field selection).
- [ ] Wire `bids_properties_from_ffprobe` into `bids/inject_sidecar.py::_do_sidecar`
      (currently `_do_sidecar` only calls `parse_bids_media_info`, not this module at all).
- [x] `split_video.py::_to_bids_model` — **resolved by moving it here**, not by making
      `split_video.py` call into `properties.py`: it's now `bids_properties_from_split_result`
      in this module (see above), and `split_video.py::_write_sidecar` calls it. Superseded the
      original plan (see [inject-sidecar-spec.md Open Questions
      #3](inject-sidecar-spec.md#open-questions--todos), which described factoring the
      mapping *out of* `split_video.py` into a shared module — this is that shared module).
- [ ] `bids_properties_from_split_result` doesn't accept a `props` accumulation parameter, unlike
      the other two `bids_properties_from_*` functions in this module — add for consistency, or
      confirm it's not needed since it's not currently composed with another source the way
      `bids_properties_from_va_record`/`bids_properties_from_ffprobe` will be.
