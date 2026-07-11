# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
BIDS media-file metadata API helpers.

Intended to provide the shared BIDS media-file field table and
AudioInfo/VideoInfo -> BIDS-dict mapping helpers, per the BEP044/media-files
proposal (bids-standard/bids-specification PR #2367):
https://bids-specification--2367.org.readthedocs.build/en/2367/appendices/media-files.html

See .ai/spec-bids-media.md for the full specification.
"""

from enum import Enum


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
