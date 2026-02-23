# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
Core logic for bids-inject: cross-reference ReproStim videos.tsv with BIDS
_scans.tsv files to slice and inject per-acquisition video clips into a BIDS
dataset.

See .ai/spec-bids-inject.md for the full specification.
"""

import logging
from enum import Enum
from typing import Callable, Optional

from pydantic import BaseModel, Field

# initialize the logger
logger = logging.getLogger(__name__)
logger.debug(f"name={__name__}")


####################################################################
# Enumerations
####################################################################


class BufferPolicy(str, Enum):
    """Policy for handling buffer overflow beyond video boundaries."""
    STRICT = "strict"
    FLEXIBLE = "flexible"


class QrMode(str, Enum):
    """QR code-based timing refinement mode."""
    NONE = "none"
    AUTO = "auto"
    EMBED_EXISTING = "embed-existing"
    PARSE = "parse"


class LayoutMode(str, Enum):
    """Output file placement layout within the BIDS dataset."""
    NEARBY = "nearby"
    TOP_STIMULI = "top-stimuli"


class MediaSuffix(str, Enum):
    """Recording-type suffix per BEP044:Stimuli."""
    VIDEO = "_video"
    AUDIO = "_audio"
    AUDIOVIDEO = "_audiovideo"


####################################################################
# Data models
####################################################################


class ScanRecord(BaseModel):
    """A single row from a BIDS _scans.tsv file."""

    filename: str = Field(..., description="Relative path to NIfTI within subject/session dir")
    acq_time: str = Field(..., description="ISO 8601 acquisition start datetime")



####################################################################
# Public API
####################################################################



def do_main(
    paths: tuple,
    videos_tsv: str,
    recursive: bool,
    buffer_before: str,
    buffer_after: str,
    buffer_policy: str,
    time_offset: float,
    qr: str,
    layout: str,
    timezone: str,
    dry_run: bool,
    verbose: bool,
    out_func: Callable,
) -> int:
    """Main entry point for the bids-inject command.

    Orchestrates loading of videos.tsv, discovery of *_scans.tsv files,
    per-scan matching, slicing, and injection.

    Args:
        paths: Tuple of paths from the CLI PATHS argument.
        videos_tsv: Path to videos.tsv produced by video-audit.
        recursive: Whether to recurse into subdirectories for *_scans.tsv discovery.
        buffer_before: Buffer before scan onset (seconds or ISO 8601).
        buffer_after: Buffer after scan end (seconds or ISO 8601).
        buffer_policy: 'strict' or 'flexible'.
        time_offset: Clock offset in seconds added to acq_time values.
        qr: QR mode string ('none', 'auto', 'embed-existing', 'parse').
        layout: Layout mode string ('nearby', 'top-stimuli').
        timezone: Timezone string ('local' or IANA name).
        dry_run: If True, analyse and resolve matches but skip split-video
                 and all file writes; print planned actions instead.
        verbose: Whether to emit verbose output.
        out_func: Output function for user-facing messages (e.g. click.echo).

    Returns:
        Exit code: 0 on success, non-zero on error.
    """
    raise NotImplementedError("do_main is not yet implemented")