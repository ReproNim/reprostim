# BIDS Media-File Properties Extraction Specification

## Overview

`properties.py` (`src/reprostim/bids/properties.py`) extracts BIDS media-file sidecar properties
(the `BidsMediaProperty` keys defined in [spec-bids-media.md](spec-bids-media.md)) from various
sources — currently `ffprobe`-derived `AudioInfo`/`VideoInfo` (via
`bids_properties_from_audio_video_info`, or directly from a file path via
`bids_properties_from_ffprobe`), and in future cached `VaRecord` rows (`videos.tsv`).

It is meant to become the **single place** `bids-inject-sidecar`, `bids-inject`, and
`split-video` all produce BIDS sidecar properties from, instead of each reimplementing the
`AudioInfo`/`VideoInfo`/`VaRecord` → BIDS-dict mapping independently — see
[spec-bids-inject-sidecar.md § Relationship to `bids-inject` /
`split-video`](spec-bids-inject-sidecar.md#relationship-to-bids-inject--split-video).

**Status: two APIs implemented and one consumer wired up.** `bids_properties_from_audio_video_info`
and `bids_properties_from_ffprobe` are done; `bids/inject.py::_call_split_video` now calls
`bids_properties_from_ffprobe` (replacing its own direct `get_audio_video_info_ffprobe` call +
manual field selection) to populate `sidecar_metadata`. `bids-inject-sidecar` (`_do_sidecar`) and
`split_video.py::_to_bids_model` have **not** been wired up yet. The `VaRecord`-based entry point
and a cache-aware/path-orchestrating wrapper covering both sources are future work (see Open
Questions).

---

## Motivation

`bids/media.py` deliberately stays close to the BEP044 spec — it's the taxonomy (enums,
`BidsMediaInfo`), not extraction logic (see [spec-bids-media.md §
Overview](spec-bids-media.md#overview)). Something still has to turn actual `ffprobe`/cache
output into `BidsMediaProperty`-keyed values, though, and that logic needs one home so
`bids-inject-sidecar` and `bids-inject`/`split-video` (`split_video.py::_to_bids_model`) stop
maintaining separate, potentially-drifting copies of the same field mapping. `properties.py` is
that home.

---

## Layering

`properties.py` depends on `bids/media.py` (for `BidsMediaProperty`) and on
`reprostim.qr.video_audit` (for `AudioInfo`/`VideoInfo`, and in future `VaRecord`) — not the
reverse. `bids/inject_sidecar.py`/`bids/inject.py` are expected to depend on `properties.py`
rather than reaching into `qr.video_audit` directly. **`bids/inject.py` does this already**
(`_call_split_video` imports `bids_properties_from_ffprobe`, not `get_audio_video_info_ffprobe`);
`bids/inject_sidecar.py` still imports `parse_bids_media_info` from `bids/media.py` only, not
`properties.py`.

> `AudioInfo`/`VideoInfo`/`VaRecord` currently live in `reprostim/qr/video_audit.py`, not yet
> moved to a `reprostim.media` package (see the broader package-reorganization discussion this
> session). `properties.py` importing from `reprostim.qr.video_audit` reflects today's layout;
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
`reprostim.qr.video_audit.get_audio_video_info_ffprobe`) to a **plain `Dict[str, Any]`** keyed by
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
[spec-bids-inject-sidecar.md](spec-bids-inject-sidecar.md)'s extraction priority order), the
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
[spec-bids-media.md](spec-bids-media.md).

### `_set_prop` (internal helper)

```python
def _set_prop(props: Dict[str, Any], key: BidsMediaProperty, value: Any) -> None: ...
```

Sets `props[key.value] = value`, skipping `None`. Factored out (not a closure inside
`bids_properties_from_audio_video_info`) specifically so the planned `VaRecord`-based function
below can reuse it.

---

## `bids_properties_from_ffprobe` (implemented)

```python
def bids_properties_from_ffprobe(
    path: str, props: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]: ...
```

Convenience wrapper: calls `reprostim.qr.video_audit.get_audio_video_info_ffprobe(path)` to get
`(AudioInfo, VideoInfo)`, then passes them (plus `props`, unchanged) straight through to
`bids_properties_from_audio_video_info` — see [Shared `props`
accumulation](#shared-props-accumulation) above.
This is the direct-from-`ffprobe` counterpart to the still-TBD `bids_properties_from_va_record`
(cache-based) below — together they'll back a single orchestrating entry point once the latter
exists.

`get_audio_video_info_ffprobe` never returns `None` for either stream — it returns a
default-constructed (all-`None`-fields) `AudioInfo`/`VideoInfo` when a stream is absent or
`ffprobe` fails — so `bids_properties_from_ffprobe` on a nonexistent/unreadable path returns `{}`
rather than raising.

---

## Open Questions / TODOs

- [ ] `bids_properties_from_va_record(record: VaRecord) -> Dict[str, Any]` — map a cached
      `videos.tsv` row (`audio_sr`, `video_res_detected`, codec columns) to the same property
      dict, for the `--videos` cache-lookup path `bids-inject-sidecar`'s spec describes.
- [ ] `get_bids_properties(path: str, va_record: Optional[VaRecord] = None) -> Dict[str, Any]` —
      single orchestrating entry point: resolve `va_record` → `bids_properties_from_va_record`,
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
- [ ] Factor `split_video.py::_to_bids_model` to use `properties.py` once the `VaRecord`/path
      orchestration entry points exist (no behavior change to existing `split-video`/`bids-inject`
      output) — see [spec-bids-inject-sidecar.md Open Questions
      #3](spec-bids-inject-sidecar.md#open-questions--todos). Note `_to_bids_model` has already
      been hand-updated to use `ImagePixelFormat`/`ImageBitDepth` (matching what
      `bids_properties_from_ffprobe` produces) even though it doesn't call into `properties.py`
      yet — the two are naming-compatible but not yet code-sharing.
