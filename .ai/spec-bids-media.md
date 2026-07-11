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

## Codec Reference

`BidsMediaCodec(str, Enum)` (implemented) is a **common, non-exhaustive** reference table of
codecs, per the BEP044/media-files proposal's Codec Identification section. Codec identification
uses two complementary naming systems:

- **FFmpeg codec names (RECOMMENDED)** — used for the `AudioCodec`/`VideoCodec` fields, auto-
  extractable via `ffprobe -v quiet -print_format json -show_streams <file>`. This is
  `BidsMediaCodec`'s enum **value**.
- **RFC 6381 codec strings (OPTIONAL)** — used for the `AudioCodecRFC6381`/`VideoCodecRFC6381`
  fields; more precise (profile/level) but only OPTIONAL. Carried as each member's `rfc6381`
  attribute. RFC 6381 strings vary by profile/level — the value stored here is only a
  *representative example*, not the only valid string for that codec.

Each member also carries a `category: BidsMediaType` (`AUDIO` or `VIDEO`) identifying which
stream kind it applies to, and `BidsMediaCodec.for_category(category)` filters by it — mirroring
`BidsMediaProperty.for_category()`'s API.

| Member       | Value (FFmpeg name) | `rfc6381`           | `category` | Notes                        |
|--------------|----------------------|-----------------------|-------------|--------------------------------|
| `H264`       | `h264`               | `avc1.640028`         | video       | Most widely supported            |
| `HEVC`       | `hevc`               | `hev1.1.6.L93.B0`     | video       | High efficiency                  |
| `VP9`        | `vp9`                | `vp09.00.10.08`       | video       | Open, royalty-free               |
| `AV1`        | `av1`                | `av01.0.01M.08`       | video       | Next-gen open codec              |
| `AAC`        | `aac`                | `mp4a.40.2`            | audio       | Default audio for MP4 (AAC-LC)   |
| `MP3`        | `mp3`                | `mp4a.6B`              | audio       | Legacy lossy audio                |
| `OPUS`       | `opus`               | `Opus`                 | audio       | Open, low-latency audio           |
| `FLAC`       | `flac`               | `fLaC`                 | audio       | Open lossless audio               |
| `PCM_S16LE`  | `pcm_s16le`          | `None`                 | audio       | Uncompressed (WAV); no RFC 6381 string |

**Not exhaustive by design**: `AudioCodec`/`VideoCodec`/`AudioCodecRFC6381`/`VideoCodecRFC6381`
are free-form strings per BEP044 — `ffprobe` can report codec names not in this table (e.g.
`prores`, `vorbis`, `alac`). `BidsMediaCodec` is a convenience reference for the common cases
listed in the BEP044 appendix, **not** a closed set used for validation; callers should not
reject an unrecognized `AudioInfo.codec`/`VideoInfo.codec` value just because it has no
`BidsMediaCodec` member.

---

## `BidsMediaInfo` (path-derived data holder)

`BidsMediaInfo(BaseModel)` (implemented) is a **pure data class** — a pydantic `BaseModel`
matching the `VaRecord`/`BiSummary` convention used elsewhere in `qr/` — holding the BIDS
media type/format info derived *from a file path*. It intentionally has **no parsing logic of
its own** (no `from_path`/constructor-time inference): populating it from an actual path is done
by the separate module-level function `parse_bids_media_info` (implemented, see below).

```python
class BidsMediaInfo(BaseModel):
    path: str
    media_type: Optional[BidsMediaType] = None
    format: Optional[Union[AudioFormat, VideoFormat, ImageFormat]] = None
    errors: List[BidsMediaInfoError] = Field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors
```

- `format` is a `Union` of the three per-category format enums (not a single flattened enum),
  since a recognized extension only ever belongs to one of `AudioFormat`/`VideoFormat`/
  `ImageFormat`.
- `errors: List[BidsMediaInfoError]` — a list, not a single error — since the future path-parsing
  function may detect **multiple, independent problems** in one path (e.g. both an unrecognized
  extension *and* a media-type/suffix mismatch) and should surface all of them, not just the
  first.
- `valid` is a **computed property** (`not self.errors`), not a stored field, so it can never
  drift out of sync with `errors`.

`BidsMediaInfoError(BaseModel)` is a small structured-error model (not a plain string), so each
recorded problem carries a machine-readable `code: BidsMediaErrorCode` alongside its
human-readable `message: str`:

| `BidsMediaErrorCode` member | Value                 | Meaning                                                                 |
|-----------------------------------|------------------------|---------------------------------------------------------------------------|
| `INVALID_PATH`                    | `invalid_path`         | The given path is malformed or has no filename/extension.                |
| `UNKNOWN_EXTENSION`                | `unknown_extension`    | The file extension is not a recognized `AudioFormat`/`VideoFormat`/`ImageFormat`. |
| `UNKNOWN_MEDIA_TYPE`               | `unknown_media_type`   | The BIDS media type could not be determined from the path.               |
| `MEDIA_TYPE_MISMATCH`              | `media_type_mismatch`  | The extension is inconsistent with the detected/declared media type (e.g. an audio-only extension on a `_video` file). Not currently produced — see Open Questions. |

---

## `parse_bids_media_info` (path-parsing function)

`parse_bids_media_info(path: str) -> BidsMediaInfo` (implemented) determines a `BidsMediaInfo`
from a file path **by name only** — no filesystem access, no `ffprobe`. Resolution order:

1. **Filename has no extension at all** (no `.` in the base name) → single `INVALID_PATH` error;
   `media_type`/`format` stay `None`. Nothing further is attempted.
2. **Extension → `format`**: the extension (lowercased) is looked up against `AudioFormat` /
   `VideoFormat` / `ImageFormat` independently of step 3. Unrecognized → `UNKNOWN_EXTENSION`
   error; `format` stays `None`. This lookup is unconditional — it runs and can error regardless
   of whether step 3 succeeds, so a path can carry both an `UNKNOWN_EXTENSION` *and* an
   `UNKNOWN_MEDIA_TYPE` error at once.
3. **Trailing `_<token>` → `media_type`** (the "entity token" for type): the filename stem's last
   `_`-delimited segment is matched case-insensitively against `BidsMediaType` values
   (`audio`/`video`/`image`/`audiovideo`). Example: `..._recording-reprostim_video.mkv` →
   `video` → `BidsMediaType.VIDEO`.
   - **Match** → `media_type` set directly, no error.
   - **No match** (missing entirely, or an unrelated token like a hand-picked filename with no
     BIDS suffix) → `UNKNOWN_MEDIA_TYPE` error recorded, **and** `media_type` falls back to a
     guess from the `format` resolved in step 2 (`AudioFormat` → `AUDIO`, `ImageFormat` →
     `IMAGE`, `VideoFormat` → `VIDEO`). If step 2 also failed to resolve a format, `media_type`
     stays `None`.

**Video-container ambiguity**: a `VideoFormat` extension (`.mp4`/`.mkv`/`.avi`/`.webm`) cannot by
itself distinguish `VIDEO` from `AUDIOVIDEO` — only the filename suffix (or actual stream
inspection) can. The extension-fallback in step 3 therefore always guesses `VIDEO` (the more
conservative option — it doesn't assert an unconfirmed audio stream) rather than `AUDIOVIDEO`.
This means an `AUDIOVIDEO` file whose filename happens to lack a valid `_audiovideo` suffix will
be misclassified as `VIDEO` by the fallback (with an `UNKNOWN_MEDIA_TYPE` error attached, so the
caller can tell the type is a guess, not a confirmed read).

**`MEDIA_TYPE_MISMATCH` is not produced by this function** — e.g. a filename ending in
`_video.wav` currently resolves `media_type=VIDEO` (from the suffix) and `format=WAV` with no
error, even though a WAV file can't actually be BIDS `_video`. Detecting that inconsistency was
explicitly out of scope for this pass (see Open Questions).

Example resolutions:

| Path                                                          | `media_type` | `format` | `errors`                              |
|-----------------------------------------------------------------|---------------|-----------|-----------------------------------------|
| `sub-01_task-rest_recording-reprostim_video.mkv`                | `VIDEO`       | `MKV`     | *(none)*                                 |
| `sub-01_task-rest_recording-reprostim_audiovideo.mp4`           | `AUDIOVIDEO`  | `MP4`     | *(none)*                                 |
| `sub-01_task-rest_myrecording.mkv` *(no valid suffix)*          | `VIDEO`*      | `MKV`     | `UNKNOWN_MEDIA_TYPE`                     |
| `sub-01_task-rest_myrecording.wav` *(no valid suffix)*          | `AUDIO`       | `WAV`     | `UNKNOWN_MEDIA_TYPE`                     |
| `sub-01_task-rest_myrecording.xyz` *(no valid suffix, bad ext)* | `None`        | `None`    | `UNKNOWN_EXTENSION`, `UNKNOWN_MEDIA_TYPE`|
| `novalidname` *(no extension)*                                  | `None`        | `None`    | `INVALID_PATH`                           |

\* guessed via the video-container-ambiguity fallback above, not confirmed.

---

## Open Questions / TODOs

- [x] `BidsMediaType` enum implemented (media-suffix names/descriptions per BEP044 appendix).
- [x] `AudioFormat` / `VideoFormat` / `ImageFormat` enums implemented (extension-keyed format
      names/descriptions per BEP044 appendix format tables).
- [x] `BidsMediaProperty` enum implemented (sidecar JSON property names + `categories` per
      BEP044 Complete Metadata Properties Table; see above).
- [x] `BidsMediaCodec` enum implemented (common FFmpeg-name/RFC-6381 codec reference +
      `category`; see [Codec Reference](#codec-reference) above). Non-exhaustive by design.
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
- [x] `BidsMediaInfo` / `BidsMediaInfoError` / `BidsMediaErrorCode` implemented as pure data
      classes (see above); no parsing logic included by design.
- [x] `parse_bids_media_info(path: str) -> BidsMediaInfo` implemented (filename-suffix +
      extension-fallback resolution; see above). Does **not** access the filesystem or `ffprobe`.
- [ ] `MEDIA_TYPE_MISMATCH` is defined but never produced by `parse_bids_media_info` — decide
      whether/how to detect it (e.g. suffix says `video` but extension is an audio-only format)
      and whether that reuses/extends `bids_inject.py::MediaSuffix`.
- [ ] Video-container ambiguity: `parse_bids_media_info`'s extension-only fallback always guesses
      `VIDEO` over `AUDIOVIDEO` for `.mp4`/`.mkv`/`.avi`/`.webm` when the filename suffix is
      missing/invalid — confirm this default is acceptable, or consider leaving `media_type=None`
      in the ambiguous case instead of guessing.
- [ ] Filename-suffix matching in `parse_bids_media_info` is case-insensitive and only inspects
      the single trailing `_<token>` — confirm this is sufficient vs. reusing/extending
      `bids_inject.py::MediaSuffix`'s parsing (which is underscore-prefixed and video/audio/
      audiovideo only, no `image`).
