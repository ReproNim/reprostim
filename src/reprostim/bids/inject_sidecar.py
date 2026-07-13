# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
Core logic for bids-inject-sidecar: extract BIDS media-file metadata from
audio/video files and write or update their ``.json`` sidecars.
"""

import logging
import os
from enum import Enum
from typing import Callable, List, Optional

from pydantic import BaseModel, Field

# initialize the logger
logger = logging.getLogger(__name__)
logger.debug(f"name={__name__}")


class OverwriteMode(str, Enum):
    """Sidecar JSON write mode for bids-inject-sidecar's ``--mode`` option."""

    REPLACE = "replace"
    """Overwrite the entire sidecar with only the freshly extracted/added
    fields."""
    UPDATE = "update"
    """Merge freshly extracted/added fields into the existing sidecar,
    preserving other existing keys untouched."""


class ConflictPolicy(str, Enum):
    """Policy for bids-inject-sidecar's ``--existing-different`` option: how
    to handle a field that already exists in the sidecar with a different,
    non-``n/a`` value."""

    ERROR = "error"
    """Abort processing that file and report the conflict."""
    OVERWRITE = "overwrite"
    """Log a warning and proceed with the new value."""


class BisContext(BaseModel):
    """Context for bids-inject-sidecar processing of scan records."""

    mode: OverwriteMode = Field(
        default=OverwriteMode.UPDATE,
        description="Sidecar JSON write mode.",
    )
    conflict_policy: ConflictPolicy = Field(
        default=ConflictPolicy.ERROR,
        description="Policy for a field with a differing existing value.",
    )


def _do_sidecar(ctx: BisContext, path: str):
    """"""
    logger.debug(f"TODO: {path}")


def _do_sidecar_all(ctx: BisContext, files: List[str]):
    # iterate over paths and depending on whether it's a file or directory,
    # process accordingly
    for path in files:
        if os.path.isfile(path):
            _do_sidecar(ctx, path)
        else:
            logger.warning(f"Skipping invalid path: {path}")


def do_main(
    files: List[str],
    videos: Optional[str],
    mode: str,
    add_meta: List[str],
    existing_different: str,
    dry_run: bool,
    verbose: bool,
    out_func: Callable,
) -> int:
    """Main entry point for the bids-inject-sidecar command.

    NOT YET IMPLEMENTED (GitHub issue #259). See .ai/spec-bids-inject-sidecar.md
    for the intended behavior: for each file in ``files``, extract BIDS
    media-file metadata (via ``videos`` cache lookup and/or ``ffprobe``), merge
    in ``add`` overrides, and write/update the corresponding ``.json`` sidecar
    according to ``mode`` and ``existing_different``.

    :param files: Audio/video file paths from the CLI ``FILES`` argument.
    :type files: List[str]
    :param videos: Optional path to ``videos.tsv`` (produced by ``video-audit``)
        used to look up cached fields instead of re-running ``ffprobe``.
    :type videos: Optional[str]
    :param mode: Sidecar write mode, ``"replace"`` or ``"update"``.
    :type mode: str
    :param add_meta: Raw ``META=VALUE`` strings from repeated ``--add`` options.
    :type add_meta: List[str]
    :param existing_different: Conflict policy when a field already exists in
        the sidecar with a different value, ``"error"`` or ``"overwrite"``.
    :type existing_different: str
    :param dry_run: When ``True``, compute but do not write any sidecar.
    :type dry_run: bool
    :param verbose: Enable verbose output.
    :type verbose: bool
    :param out_func: Callable used to print user-facing output (e.g. ``click.echo``).
    :type out_func: Callable
    :return: Exit code (0 on success, non-zero on error).
    :rtype: int
    """

    ctx: BisContext = BisContext(
        mode=OverwriteMode(mode),
        conflict_policy=ConflictPolicy(existing_different),
    )
    _do_sidecar_all(ctx, files)

    return 0
