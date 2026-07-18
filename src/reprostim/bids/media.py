# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
BIDS media-file metadata API helpers.

Intended to provide the shared BIDS media-file field table and
AudioInfo/VideoInfo -> BIDS-dict mapping helpers, per the BEP044/media-files
proposal (bids-standard/bids-specification PR #2367):
https://bids-specification--2367.org.readthedocs.build/en/2367/appendices/media-files.html

See .ai/bids/media-spec.md for the full specification.
"""

from enum import Enum
from pathlib import PurePath
from typing import FrozenSet, List, Optional, Union

from pydantic import BaseModel, Field

#######################################################
# Enums


class BidsMediaType(str, Enum):
    """BIDS media-file suffix, per the BEP044/media-files proposal
    (bids-standard/bids-specification PR #2367)."""

    AUDIO = "audio"
    """An audio data file containing one or more audio streams.
    Common formats include WAV (uncompressed), MP3, AAC, and
    Ogg Vorbis."""
    AUDIOVIDEO = "audiovideo"
    """A media file containing both audio and video streams.
    Common containers include MP4, MKV, AVI, and WebM."""
    IMAGE = "image"
    """A still image data file. Common formats include JPEG,
    PNG, SVG, WebP, and TIFF."""
    VIDEO = "video"
    """A video data file containing one or more video streams
    but no audio. Common containers include MP4, MKV, AVI, and
    WebM."""


class AudioFormat(str, Enum):
    """Audio file format, identified by its file extension
    (without the leading dot), per the BEP044/media-files
    proposal (bids-standard/bids-specification PR #2367)."""

    WAV = "wav"
    """A Waveform Audio File Format audio file, typically
    containing uncompressed PCM audio."""
    FLAC = "flac"
    """A FLAC lossless audio file."""
    MP3 = "mp3"
    """An MP3 audio file."""
    AAC = "aac"
    """An Advanced Audio Coding audio file."""
    OGG = "ogg"
    """An Ogg audio file, typically containing Vorbis-encoded
    audio."""


class ImageFormat(str, Enum):
    """Image file format, identified by its file extension
    (without the leading dot), per the BEP044/media-files
    proposal (bids-standard/bids-specification PR #2367)."""

    JPG = "jpg"
    """A JPEG image file."""
    PNG = "png"
    """A Portable Network Graphics file."""
    SVG = "svg"
    """A Scalable Vector Graphics image file."""
    WEBP = "webp"
    """A WebP image file."""
    TIF = "tif"
    """A Tag Image File Format file."""
    TIFF = "tiff"
    """A Tag Image File Format image file. The .tiff extension is
    the long form of .tif."""


class VideoFormat(str, Enum):
    """Video container format, identified by its file extension
    (without the leading dot), per the BEP044/media-files
    proposal (bids-standard/bids-specification PR #2367)."""

    MP4 = "mp4"
    """An MPEG-4 Part 14 media container file."""
    AVI = "avi"
    """An Audio Video Interleave media container file."""
    MKV = "mkv"
    """A Matroska media container file."""
    WEBM = "webm"
    """A WebM media container file, typically containing VP8/VP9
    video and Vorbis/Opus audio."""


class BidsMediaCodec(str, Enum):
    """Common codec reference, per the BEP044/media-files proposal's
    Codec Identification section (bids-standard/bids-specification
    PR #2367). Each member's value is the FFmpeg codec name — the
    RECOMMENDED value for the ``AudioCodec``/``VideoCodec`` fields,
    auto-extractable via ``ffprobe -v quiet -print_format json
    -show_streams <file>``. ``rfc6381`` is a representative RFC 6381
    codec string (OPTIONAL; used for ``AudioCodecRFC6381``/
    ``VideoCodecRFC6381`` — actual strings vary by profile/level, so
    this is only an example value), and ``category`` is the
    :class:`BidsMediaType` stream kind (``AUDIO`` or ``VIDEO``) the
    codec applies to.

    Not exhaustive: ``AudioCodec``/``VideoCodec`` accept any FFmpeg
    codec name as a free string; this enum only covers the common
    codecs listed in the BEP044 reference table."""

    def __new__(cls, value: str, rfc6381: Optional[str], category: BidsMediaType):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.rfc6381 = rfc6381
        obj.category = category
        return obj

    H264 = ("h264", "avc1.640028", BidsMediaType.VIDEO)
    """H.264 / AVC. Most widely supported."""
    HEVC = ("hevc", "hev1.1.6.L93.B0", BidsMediaType.VIDEO)
    """H.265 / HEVC. High efficiency."""
    VP9 = ("vp9", "vp09.00.10.08", BidsMediaType.VIDEO)
    """VP9. Open, royalty-free."""
    AV1 = ("av1", "av01.0.01M.08", BidsMediaType.VIDEO)
    """AV1. Next-gen open codec."""
    AAC = ("aac", "mp4a.40.2", BidsMediaType.AUDIO)
    """AAC-LC. Default audio for MP4."""
    MP3 = ("mp3", "mp4a.6B", BidsMediaType.AUDIO)
    """MP3. Legacy lossy audio."""
    OPUS = ("opus", "Opus", BidsMediaType.AUDIO)
    """Opus. Open, low-latency audio."""
    FLAC = ("flac", "fLaC", BidsMediaType.AUDIO)
    """FLAC. Open lossless audio."""
    PCM_S16LE = ("pcm_s16le", None, BidsMediaType.AUDIO)
    """PCM 16-bit LE. Uncompressed (WAV). No RFC 6381 string."""

    @classmethod
    def for_category(cls, category: BidsMediaType) -> List["BidsMediaCodec"]:
        """Return all codecs applicable to the given stream category (AUDIO or VIDEO)."""
        return [member for member in cls if member.category == category]


class BidsMediaErrorCode(str, Enum):
    """Category of problem that can be detected while determining a
    :class:`BidsMediaInfo` from a file path. Populated by a separate
    path-parsing module function (not part of this data class)."""

    INVALID_PATH = "invalid_path"
    """The given path is malformed or has no filename/extension."""
    UNKNOWN_EXTENSION = "unknown_extension"
    """The file extension is not a recognized Audio/Video/Image
    format."""
    UNKNOWN_MEDIA_TYPE = "unknown_media_type"
    """The BIDS media type could not be determined from the path."""
    MEDIA_TYPE_MISMATCH = "media_type_mismatch"
    """The file extension is inconsistent with the detected/declared
    media type (e.g. an audio-only extension on a ``_video`` file)."""


class BidsMediaProperty(str, Enum):
    """BIDS media-file sidecar metadata property, per the
    BEP044/media-files proposal (bids-standard/bids-specification
    PR #2367). Each member's value is the exact sidecar JSON key;
    ``categories`` lists the :class:`BidsMediaType` suffix(es) the
    property applies to, so properties can be filtered by category
    via :meth:`for_category`."""

    def __new__(cls, value: str, categories: FrozenSet[BidsMediaType]):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj.categories = categories
        return obj

    RECORDING_DURATION = (
        "RecordingDuration",
        frozenset({BidsMediaType.AUDIO, BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO}),
    )
    """Length of the recording in seconds."""

    AUDIO_CODEC = (
        "AudioCodec",
        frozenset({BidsMediaType.AUDIO, BidsMediaType.AUDIOVIDEO}),
    )
    """Audio codec as FFmpeg name (e.g. "aac", "mp3", "opus")."""

    AUDIO_SAMPLE_RATE = (
        "AudioSampleRate",
        frozenset({BidsMediaType.AUDIO, BidsMediaType.AUDIOVIDEO}),
    )
    """Sampling frequency of the audio stream, in Hz."""

    AUDIO_CHANNEL_COUNT = (
        "AudioChannelCount",
        frozenset({BidsMediaType.AUDIO, BidsMediaType.AUDIOVIDEO}),
    )
    """Number of audio channels."""

    AUDIO_BIT_DEPTH = (
        "AudioBitDepth",
        frozenset({BidsMediaType.AUDIO, BidsMediaType.AUDIOVIDEO}),
    )
    """Number of bits per sample in the audio stream."""

    AUDIO_CODEC_RFC6381 = (
        "AudioCodecRFC6381",
        frozenset({BidsMediaType.AUDIO, BidsMediaType.AUDIOVIDEO}),
    )
    """Audio codec as an RFC 6381 string (e.g. "mp4a.40.2" for AAC-LC)."""

    IMAGE_WIDTH = (
        "ImageWidth",
        frozenset({BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO, BidsMediaType.IMAGE}),
    )
    """Width of the video frame or image, in pixels."""

    IMAGE_HEIGHT = (
        "ImageHeight",
        frozenset({BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO, BidsMediaType.IMAGE}),
    )
    """Height of the video frame or image, in pixels."""

    IMAGE_PIXEL_FORMAT = (
        "ImagePixelFormat",
        frozenset({BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO, BidsMediaType.IMAGE}),
    )
    """Pixel format per FFmpeg pix_fmt (e.g. "yuv420p", "rgb24")."""

    IMAGE_BIT_DEPTH = (
        "ImageBitDepth",
        frozenset({BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO, BidsMediaType.IMAGE}),
    )
    """Bit depth per channel of the stored pixel data."""

    VIDEO_CODEC = (
        "VideoCodec",
        frozenset({BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO}),
    )
    """Video codec as FFmpeg name (e.g. "h264", "hevc", "vp9")."""

    VIDEO_FRAME_RATE = (
        "VideoFrameRate",
        frozenset({BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO}),
    )
    """Video frame rate of the video stream, in Hz."""

    VIDEO_FRAME_COUNT = (
        "VideoFrameCount",
        frozenset({BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO}),
    )
    """Total number of frames in the video stream."""

    VIDEO_CODEC_RFC6381 = (
        "VideoCodecRFC6381",
        frozenset({BidsMediaType.VIDEO, BidsMediaType.AUDIOVIDEO}),
    )
    """Video codec as an RFC 6381 string (e.g. "avc1.640028" for H.264)."""

    @classmethod
    def for_category(cls, category: BidsMediaType) -> List["BidsMediaProperty"]:
        """Return all properties that apply to the given media category."""
        return [member for member in cls if category in member.categories]


#######################################################
# Classes


class BidsMediaInfoError(BaseModel):
    """A single problem detected while determining a
    :class:`BidsMediaInfo` from a file path."""

    code: BidsMediaErrorCode = Field(description="Category of the problem.")
    message: str = Field(description="Human-readable detail about the problem.")


class BidsMediaInfo(BaseModel):
    """BIDS media type/format info derived from a file path, per the
    BEP044/media-files proposal. Pure data holder — populated by a
    separate path-parsing module function, not a method on this
    class."""

    path: str = Field(description="Input file path this info was derived from.")
    media_type: Optional[BidsMediaType] = Field(
        default=None,
        description="Detected BIDS media type (audio/video/image/audiovideo), "
        "if determined.",
    )
    format: Optional[Union[AudioFormat, VideoFormat, ImageFormat]] = Field(
        default=None,
        description="Detected concrete file format, if recognized.",
    )
    errors: List[BidsMediaInfoError] = Field(
        default_factory=list,
        description="All problems detected while parsing the path, if any.",
    )

    @property
    def valid(self) -> bool:
        """True when no errors were detected."""
        return not self.errors


#######################################################
# Functions


def _format_from_extension(
    ext: str,
) -> Optional[Union[AudioFormat, VideoFormat, ImageFormat]]:
    """Look up a (lowercase, dot-less) file extension in
    AudioFormat/VideoFormat/ImageFormat."""
    for format_cls in (AudioFormat, VideoFormat, ImageFormat):
        try:
            return format_cls(ext)
        except ValueError:
            continue
    return None


def _media_type_from_format(
    media_format: Optional[Union[AudioFormat, VideoFormat, ImageFormat]]
) -> Optional[BidsMediaType]:
    """Best-effort BidsMediaType for a format determined by extension alone.

    VideoFormat is inherently ambiguous between VIDEO and AUDIOVIDEO from the
    extension alone (a .mp4/.mkv/.avi/.webm container may or may not carry an
    audio stream); VIDEO is used as the conservative default rather than
    asserting an audio stream that hasn't been confirmed.
    """
    if isinstance(media_format, AudioFormat):
        return BidsMediaType.AUDIO
    if isinstance(media_format, ImageFormat):
        return BidsMediaType.IMAGE
    if isinstance(media_format, VideoFormat):
        return BidsMediaType.VIDEO
    return None


def parse_bids_media_info(path: str) -> BidsMediaInfo:
    """Determine a :class:`BidsMediaInfo` from a file path, by name only (no
    filesystem access).

    The BIDS media type is primarily read from the filename's trailing
    ``_<suffix>`` token (e.g. ``..._video.mkv`` -> ``BidsMediaType.VIDEO``). If
    that token is missing or not a valid :class:`BidsMediaType` value, a
    ``UNKNOWN_MEDIA_TYPE`` error is recorded and the media type is instead
    guessed from the file extension (see :func:`_media_type_from_format`). The
    file extension is always independently resolved to a format
    (``AudioFormat``/``VideoFormat``/``ImageFormat``); an unrecognized
    extension is recorded as an ``UNKNOWN_EXTENSION`` error regardless of
    whether the media type was resolved from the filename suffix.
    """
    name = PurePath(path).name
    if not name or "." not in name:
        return BidsMediaInfo(
            path=path,
            errors=[
                BidsMediaInfoError(
                    code=BidsMediaErrorCode.INVALID_PATH,
                    message=f"path {path!r} has no filename/extension to parse",
                )
            ],
        )

    stem, _, ext_raw = name.rpartition(".")
    ext = ext_raw.lower()
    errors: List[BidsMediaInfoError] = []

    media_format = _format_from_extension(ext)
    if media_format is None:
        errors.append(
            BidsMediaInfoError(
                code=BidsMediaErrorCode.UNKNOWN_EXTENSION,
                message=f"'.{ext}' is not a recognized audio/video/image extension",
            )
        )

    suffix_token = stem.rsplit("_", 1)[-1] if stem else ""
    try:
        media_type: Optional[BidsMediaType] = BidsMediaType(suffix_token.lower())
    except ValueError:
        known = "/".join(t.value for t in BidsMediaType)
        errors.append(
            BidsMediaInfoError(
                code=BidsMediaErrorCode.UNKNOWN_MEDIA_TYPE,
                message=f"filename has no valid BIDS media type suffix ({known}); "
                f"found {suffix_token!r} instead, falling back to extension",
            )
        )
        media_type = _media_type_from_format(media_format)

    return BidsMediaInfo(
        path=path, media_type=media_type, format=media_format, errors=errors
    )
