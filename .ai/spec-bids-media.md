# BIDS Media-File Metadata Helpers Specification

## Overview

`bids_media.py` (`src/reprostim/qr/bids_media.py`) is a proposed shared module providing BIDS
media-file metadata API helpers: the canonical field-name/type table and
`AudioInfo`/`VideoInfo` -> BIDS-dict mapping logic, per the BEP044/media-files proposal
([bids-standard/bids-specification PR
#2367](https://bids-specification--2367.org.readthedocs.build/en/2367/appendices/media-files.html)).

**Status: stub.** Only the enums (`BidsMediaType`, `AudioFormat`, `VideoFormat`, `ImageFormat`;
see below) are implemented so far; the field table and mapping helpers are still TBD. This
document is a placeholder to be fleshed out further once that remaining scope is decided.

Relevant to: https://github.com/ReproNim/reprostim/issues/14

---

## Motivation

Both `split_video.py` (`_to_bids_model`) and the proposed `bids-inject-sidecar` command need the
same BIDS media-file field names, types, and `ffprobe`-derived-info mappings. Today that logic
lives inline in `split_video.py`. `bids_media.py` is meant to become the single source of truth
both consumers share, instead of duplicating/drifting field tables.

See [spec-bids-inject-sidecar.md § File / Module
Structure](spec-bids-inject-sidecar.md#file--module-structure) and [§ Relationship to
`bids-inject` / `split-video`](spec-bids-inject-sidecar.md#relationship-to-bids-inject--split-video)
for where this module was first proposed.

---

## Scope

TBD. Expected to cover, at minimum:

- The BIDS media-file field table (name, type, applies-to) from the BEP044 draft.
- Mapping helpers from `video_audit.py`'s `AudioInfo`/`VideoInfo` to BIDS-field dicts.

Out of scope for now: image-file (`_image` suffix) field-table entries — see [BIDS Media-File
Metadata Fields](spec-bids-inject-sidecar.md#bids-media-file-metadata-fields) note on deferred
image support. (The `image` *media type* itself is represented in `BidsMediaType` below, since
the BEP044 media-suffix table defines it regardless of field-table support.)

---

## BIDS Media Types

`BidsMediaType(str, Enum)` (implemented) enumerates the four media suffixes defined by the
BEP044/media-files proposal:

| Member       | Value        | Description                                                                                                  |
|--------------|--------------|----------------------------------------------------------------------------------------------------------------|
| `AUDIO`      | `audio`      | An audio data file containing one or more audio streams. Common formats include WAV (uncompressed), MP3, AAC, and Ogg Vorbis. |
| `AUDIOVIDEO` | `audiovideo` | A media file containing both audio and video streams. Common containers include MP4, MKV, AVI, and WebM.       |
| `IMAGE`      | `image`      | A still image data file. Common formats include JPEG, PNG, SVG, WebP, and TIFF.                                |
| `VIDEO`      | `video`      | A video data file containing one or more video streams but no audio. Common containers include MP4, MKV, AVI, and WebM. |

> **Relationship to `bids_inject.py::MediaSuffix`.** `bids_inject.py` already has a
> `MediaSuffix(str, Enum)` with values `_video` / `_audio` / `_audiovideo` (underscore-prefixed
> BIDS filename suffixes, e.g. `..._recording-reprostim_video.mkv`, and no `image` member).
> `BidsMediaType` is deliberately a separate, unprefixed enum matching the BEP044 appendix
> table's bare names and includes `image`. Reconciling/merging the two (e.g. having
> `bids_inject.py` import `BidsMediaType` instead of keeping its own enum) is left as an open
> question below rather than done as part of this change, to avoid an unrequested behavior change
> to `bids-inject`.

---

## Format Enums

Three additional enums (implemented) identify concrete file formats by extension — **value is
the bare extension, no leading dot** (e.g. `"wav"`, not `".wav"`) — per the BEP044 appendix's
format tables:

`AudioFormat(str, Enum)`:

| Member | Value  | Description                                                                          |
|--------|--------|-----------------------------------------------------------------------------------------|
| `WAV`  | `wav`  | A Waveform Audio File Format audio file, typically containing uncompressed PCM audio.  |
| `FLAC` | `flac` | A FLAC lossless audio file.                                                              |
| `MP3`  | `mp3`  | An MP3 audio file.                                                                        |
| `AAC`  | `aac`  | An Advanced Audio Coding audio file.                                                     |
| `OGG`  | `ogg`  | An Ogg audio file, typically containing Vorbis-encoded audio.                            |

`VideoFormat(str, Enum)` (video *container* formats):

| Member | Value  | Description                                                                          |
|--------|--------|-----------------------------------------------------------------------------------------|
| `MP4`  | `mp4`  | An MPEG-4 Part 14 media container file.                                                 |
| `AVI`  | `avi`  | An Audio Video Interleave media container file.                                         |
| `MKV`  | `mkv`  | A Matroska media container file.                                                        |
| `WEBM` | `webm` | A WebM media container file, typically containing VP8/VP9 video and Vorbis/Opus audio.  |

`ImageFormat(str, Enum)`:

| Member | Value  | Description                                                                          |
|--------|--------|-----------------------------------------------------------------------------------------|
| `JPG`  | `jpg`  | A JPEG image file.                                                                        |
| `PNG`  | `png`  | A Portable Network Graphics file.                                                        |
| `SVG`  | `svg`  | A Scalable Vector Graphics image file.                                                   |
| `WEBP` | `webp` | A WebP image file.                                                                        |
| `TIF`  | `tif`  | A Tag Image File Format file.                                                            |
| `TIFF` | `tiff` | A Tag Image File Format image file. The `.tiff` extension is the long form of `.tif`.   |

---

## Open Questions / TODOs

- [x] `BidsMediaType` enum implemented (media-suffix names/descriptions per BEP044 appendix).
- [x] `AudioFormat` / `VideoFormat` / `ImageFormat` enums implemented (extension-keyed format
      names/descriptions per BEP044 appendix format tables).
- [ ] Confirm final scope/API surface for the remaining field-table/mapping helpers (functions
      vs. constants vs. a small class).
- [ ] Decide field-naming convention (unprefixed `Width`/`Height`/... vs. BEP044's
      `ImageWidth`/`ImageHeight`/... — see [spec-bids-inject-sidecar.md Open Questions
      #4](spec-bids-inject-sidecar.md#open-questions--todos)).
- [ ] Factor `split_video.py::_to_bids_model` to use this module once implemented.
- [ ] Reconcile `BidsMediaType` with `bids_inject.py::MediaSuffix` (see note above) — decide
      whether `bids_inject.py` should adopt `BidsMediaType` instead of its own enum.
