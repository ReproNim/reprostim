# BIDS Media-File Metadata Helpers Specification

## Overview

`bids_media.py` (`src/reprostim/qr/bids_media.py`) is a proposed shared module providing BIDS
media-file metadata API helpers: the canonical field-name/type table and
`AudioInfo`/`VideoInfo` -> BIDS-dict mapping logic, per the BEP044/media-files proposal
([bids-standard/bids-specification PR
#2367](https://bids-specification--2367.org.readthedocs.build/en/2367/appendices/media-files.html)).

**Status: stub.** The enums (`BidsMediaType`, `AudioFormat`, `VideoFormat`, `ImageFormat`,
`BidsMediaProperty`; see below) are implemented; the `AudioInfo`/`VideoInfo` -> BIDS-dict mapping
helpers are still TBD. This document is a placeholder to be fleshed out further once that
remaining scope is decided.

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

- [x] The BIDS media-file property table (name, applies-to categories) from the BEP044 draft —
      `BidsMediaProperty`, see below.
- [ ] Declared value types (`integer`/`number`/`string`) per property — not yet carried on
      `BidsMediaProperty`; see Open Questions.
- [ ] Mapping helpers from `video_audit.py`'s `AudioInfo`/`VideoInfo` to BIDS-field dicts — TBD.

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

## BIDS Media Properties

`BidsMediaProperty(str, Enum)` (implemented) enumerates the sidecar JSON metadata properties
defined by the BEP044/media-files proposal's [Complete Metadata Properties
Table](https://bids-specification--2367.org.readthedocs.build/en/2367/appendices/media-files.html),
fetched directly from the live draft. Each member's **value is the exact sidecar JSON key**
(e.g. `"AudioCodec"`), and each member carries a `categories: FrozenSet[BidsMediaType]` attribute
listing which media type(s) the property applies to. `BidsMediaProperty.for_category(category)`
returns the list of properties applicable to a given `BidsMediaType`.

| Member                  | Value               | Categories                   | Requirement (draft) | Description                                                       |
|--------------------------|----------------------|-------------------------------|----------------------|------------------------------------------------------------------|
| `RECORDING_DURATION`     | `RecordingDuration`  | audio, video, audiovideo      | RECOMMENDED          | Length of the recording in seconds.                                |
| `AUDIO_CODEC`            | `AudioCodec`         | audio, audiovideo             | RECOMMENDED          | Audio codec as FFmpeg name (e.g. `"aac"`, `"mp3"`, `"opus"`).      |
| `AUDIO_SAMPLE_RATE`      | `AudioSampleRate`    | audio, audiovideo             | RECOMMENDED          | Sampling frequency of the audio stream, in Hz.                     |
| `AUDIO_CHANNEL_COUNT`    | `AudioChannelCount`  | audio, audiovideo             | RECOMMENDED          | Number of audio channels.                                          |
| `AUDIO_BIT_DEPTH`        | `AudioBitDepth`      | audio, audiovideo             | OPTIONAL             | Number of bits per sample in the audio stream.                     |
| `AUDIO_CODEC_RFC6381`    | `AudioCodecRFC6381`  | audio, audiovideo             | OPTIONAL             | Audio codec as an RFC 6381 string (e.g. `"mp4a.40.2"` for AAC-LC). |
| `IMAGE_WIDTH`            | `ImageWidth`         | video, audiovideo, image      | RECOMMENDED          | Width of the video frame or image, in pixels.                      |
| `IMAGE_HEIGHT`           | `ImageHeight`        | video, audiovideo, image      | RECOMMENDED          | Height of the video frame or image, in pixels.                     |
| `IMAGE_PIXEL_FORMAT`     | `ImagePixelFormat`   | video, audiovideo, image      | OPTIONAL             | Pixel format per FFmpeg `pix_fmt` (e.g. `"yuv420p"`, `"rgb24"`).   |
| `IMAGE_BIT_DEPTH`        | `ImageBitDepth`      | video, audiovideo, image      | OPTIONAL             | Bit depth per channel of the stored pixel data.                    |
| `VIDEO_CODEC`            | `VideoCodec`         | video, audiovideo              | RECOMMENDED          | Video codec as FFmpeg name (e.g. `"h264"`, `"hevc"`, `"vp9"`).     |
| `VIDEO_FRAME_RATE`       | `VideoFrameRate`     | video, audiovideo              | RECOMMENDED          | Video frame rate of the video stream, in Hz.                       |
| `VIDEO_FRAME_COUNT`      | `VideoFrameCount`    | video, audiovideo              | RECOMMENDED          | Total number of frames in the video stream.                        |
| `VIDEO_CODEC_RFC6381`    | `VideoCodecRFC6381`  | video, audiovideo              | OPTIONAL             | Video codec as an RFC 6381 string (e.g. `"avc1.640028"` for H.264).|

> **This table supersedes `spec-bids-inject-sidecar.md`'s field table in two ways**, since it was
> pulled from the live draft rather than transcribed by hand:
> 1. **Field naming**: uses the draft's actual `ImageWidth`/`ImageHeight`/`ImagePixelFormat`/
>    `ImageBitDepth` names, not the unprefixed `Width`/`Height`/`PixelFormat`/`BitDepth` that
>    `spec-bids-inject-sidecar.md` documents as its *initial-implementation* choice (see that
>    spec's [Open Questions #4](spec-bids-inject-sidecar.md#open-questions--todos)). This does
>    not itself change `bids-inject-sidecar`'s behavior — that command doesn't consume
>    `bids_media.py` yet — but it does mean the naming reconciliation those Open Questions
>    anticipate is effectively pre-decided in favor of the `Image*`-prefixed names once/if
>    `bids-inject-sidecar` or `split_video.py` adopt this module.
> 2. **`RecordingDuration` categories**: the live draft scopes it to audio/video/audiovideo only
>    (no `image`), whereas `spec-bids-inject-sidecar.md`'s table listed audio/video/image.
>
> The ReproStim-specific extras `Device`, `DeviceSerialNumber`, `TaskName` (not part of BEP044,
> only listed in `spec-bids-inject-sidecar.md`) are intentionally **not** included in
> `BidsMediaProperty`, since this enum tracks the BEP044 draft itself.

---

## Open Questions / TODOs

- [x] `BidsMediaType` enum implemented (media-suffix names/descriptions per BEP044 appendix).
- [x] `AudioFormat` / `VideoFormat` / `ImageFormat` enums implemented (extension-keyed format
      names/descriptions per BEP044 appendix format tables).
- [x] `BidsMediaProperty` enum implemented (sidecar JSON property names + `categories` per
      BEP044 Complete Metadata Properties Table; see above).
- [ ] Add declared value type (`int`/`float`/`str`) per `BidsMediaProperty` member, needed for
      `--add META=VALUE` casting in `bids-inject-sidecar` — not yet carried on the enum.
- [ ] Confirm final scope/API surface for the remaining `AudioInfo`/`VideoInfo` mapping helpers
      (functions vs. constants vs. a small class).
- [x] Field-naming convention for `BidsMediaProperty` decided: `Image*`-prefixed, matching the
      live BEP044 draft (see note above). Still needs reconciling with
      `spec-bids-inject-sidecar.md`'s unprefixed `Width`/`Height`/`PixelFormat`/`BitDepth` and
      `split_video.py::_to_bids_model`'s current output — see [spec-bids-inject-sidecar.md Open
      Questions #4](spec-bids-inject-sidecar.md#open-questions--todos).
- [ ] Factor `split_video.py::_to_bids_model` to use this module once mapping helpers exist.
- [ ] Reconcile `BidsMediaType` with `bids_inject.py::MediaSuffix` (see note above) — decide
      whether `bids_inject.py` should adopt `BidsMediaType` instead of its own enum.
