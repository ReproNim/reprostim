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
