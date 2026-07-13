# BIDS Media-File Properties Extraction Specification

## Overview

`properties.py` (`src/reprostim/bids/properties.py`) extracts BIDS media-file sidecar properties
(the `BidsMediaProperty` keys defined in [spec-bids-media.md](spec-bids-media.md)) from various
sources — currently `ffprobe`-derived `AudioInfo`/`VideoInfo` (via
`bids_properties_from_audio_video_info`), and in future cached `VaRecord` rows (`videos.tsv`) and
file paths.

It is meant to become the **single place** `bids-inject-sidecar`, `bids-inject`, and
`split-video` all produce BIDS sidecar properties from, instead of each reimplementing the
`AudioInfo`/`VideoInfo`/`VaRecord` → BIDS-dict mapping independently — see
[spec-bids-inject-sidecar.md § Relationship to `bids-inject` /
`split-video`](spec-bids-inject-sidecar.md#relationship-to-bids-inject--split-video).

**Status: first API implemented.** `bids_properties_from_audio_video_info` is done; the
`VaRecord`-based and path-orchestrating entry points are future work (see Open Questions).

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
rather than reaching into `qr.video_audit` directly.

> `AudioInfo`/`VideoInfo`/`VaRecord` currently live in `reprostim/qr/video_audit.py`, not yet
> moved to a `reprostim.media` package (see the broader package-reorganization discussion this
> session). `properties.py` importing from `reprostim.qr.video_audit` reflects today's layout;
> only that one import line needs updating if/when `video_audit.py` moves.

---

## `bids_properties_from_audio_video_info` (implemented)

```python
def bids_properties_from_audio_video_info(
    audio: Optional[AudioInfo], video: Optional[VideoInfo]
) -> Dict[str, Any]: ...
```

Maps `ffprobe`-derived `AudioInfo`/`VideoInfo` (from
`reprostim.qr.video_audit.get_audio_video_info_ffprobe`) to a **plain `Dict[str, Any]`** keyed by
the exact BIDS sidecar JSON key (`BidsMediaProperty.value`, e.g. `"AudioCodec"`) — not by the
enum member itself, so the result can be merged/serialized directly without an extra
`.value` step at every call site.

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
| `VIDEO_FRAME_COUNT`   | **not populated** — `VideoInfo` has no frame-count field (see Open Questions) |

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

## Open Questions / TODOs

- [ ] `bids_properties_from_va_record(record: VaRecord) -> Dict[str, Any]` — map a cached
      `videos.tsv` row (`audio_sr`, `video_res_detected`, codec columns) to the same property
      dict, for the `--videos` cache-lookup path `bids-inject-sidecar`'s spec describes.
- [ ] `get_bids_properties(path: str, va_record: Optional[VaRecord] = None) -> Dict[str, Any]` —
      single orchestrating entry point: resolve `va_record` → `bids_properties_from_va_record`,
      else run `ffprobe` → `bids_properties_from_audio_video_info`. This is what
      `bids-inject-sidecar`'s `_do_sidecar` should eventually call instead of invoking
      `parse_bids_media_info`/`ffprobe` itself.
- [ ] `VIDEO_FRAME_COUNT` has no direct `ffprobe`-derived source in `VideoInfo` — decide whether
      to add a frame-count field to `VideoInfo`/`get_audio_video_info_ffprobe` upstream, or
      approximate it (`fps × duration_sec`) rather than leave it unset (currently: left unset).
- [ ] `RecordingDuration` precedence when both `audio.duration_sec` and `video.duration_sec` are
      present but differ (currently: video wins unconditionally) — confirm this is the right
      default, or whether a mismatch should itself be surfaced somehow.
- [ ] Wire `bids_properties_from_audio_video_info` into `bids/inject_sidecar.py::_do_sidecar`
      (currently `_do_sidecar` only calls `parse_bids_media_info`, not this module at all).
- [ ] Factor `split_video.py::_to_bids_model` to use `properties.py` once the `VaRecord`/path
      orchestration entry points exist (no behavior change to existing `split-video`/`bids-inject`
      output) — see [spec-bids-inject-sidecar.md Open Questions
      #3](spec-bids-inject-sidecar.md#open-questions--todos).
