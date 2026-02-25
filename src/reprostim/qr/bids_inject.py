# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
Core logic for bids-inject: cross-reference ReproStim videos.tsv with BIDS
_scans.tsv files to slice and inject per-acquisition video clips into a BIDS
dataset.

See .ai/spec-bids-inject.md for the full specification.
"""

import csv
import logging
import os
from enum import Enum
from typing import Callable, List, Optional

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


class BiContext(BaseModel):
    """Context for bids-inject processing of scan records."""

    dry_run: bool = Field(
        ..., description="Whether to skip actual file writes and print planned actions"
    )
    recursive: bool = Field(
        ..., description="Whether to search for _scans.tsv files recursively"
    )


class ScanRecord(BaseModel):
    """A single row from a BIDS _scans.tsv file."""

    filename: str = Field(
        ..., description="Relative path to NIfTI within subject/session dir"
    )
    acq_time: str = Field(..., description="ISO 8601 acquisition start datetime")
    operator: Optional[str] = Field(None, description="Operator name or 'n/a'")
    randstr: Optional[str] = Field(None, description="Random string identifier")


####################################################################
# Internal API
####################################################################


def _is_scans_file(path: str) -> bool:
    """Check if the given path points to a BIDS ``*_scans.tsv`` file.

    Returns ``True`` only when *path* refers to an existing regular file
    whose name ends with ``_scans.tsv``.

    :param path: Path to test.
    :type path: str
    :returns: ``True`` if *path* is an existing ``*_scans.tsv`` file,
        ``False`` otherwise.
    :rtype: bool
    """
    return os.path.isfile(path) and path.endswith("_scans.tsv")


def _parse_scans(path: str) -> List[ScanRecord]:
    """Parse a *_scans.tsv file and return a list of ScanRecord instances.

    Reads a tab-separated BIDS scans file. The columns ``filename`` and
    ``acq_time`` are required; ``operator`` and ``randstr`` are read when
    present and left as ``None`` otherwise.

    :param path: Absolute or relative path to a ``*_scans.tsv`` file.
    :type path: str
    :returns: List of scan records parsed from the file, one per data row.
    :rtype: List[ScanRecord]
    :raises FileNotFoundError: If *path* does not exist.
    :raises KeyError: If a required column (``filename`` or ``acq_time``) is
        missing from the TSV header.
    """
    records: List[ScanRecord] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            records.append(
                ScanRecord(
                    filename=row["filename"],
                    acq_time=row["acq_time"],
                    operator=row.get("operator"),
                    randstr=row.get("randstr"),
                )
            )
    logger.debug(f"Parsed {len(records)} scan records from: {path}")
    return records


def _do_inject_scans(ctx: BiContext, path: str):
    """Process all scan records from a single ``*_scans.tsv`` file.

    Verifies that *path* is a valid BIDS scans file and delegates per-record
    injection logic.  Non-matching paths are logged as warnings and skipped.

    :param ctx: Processing context carrying flags such as ``dry_run``.
    :type ctx: BiContext
    :param path: Path to the ``*_scans.tsv`` file to process.
    :type path: str
    """
    if _is_scans_file(path):
        logger.info(f"Processing scans file: {path}")
        scans = _parse_scans(path)
        for scan in scans:
            logger.info(f"Processing scan record: {scan}")
    else:
        logger.warning(f"Skipping non-_scans.tsv file: {path}")


def _do_inject_dir(ctx: BiContext, path: str):
    """Process all ``*_scans.tsv`` files found directly inside a directory.

    Iterates over the immediate entries of *path*.  Regular files are passed
    to :func:`_do_inject_scans` (which filters for ``*_scans.tsv`` names).
    Subdirectories are recursed into only when ``ctx.recursive`` is ``True``.

    :param ctx: Processing context; ``ctx.recursive`` controls whether
        subdirectories are visited.
    :type ctx: BiContext
    :param path: Path to the directory to scan.
    :type path: str
    """

    logger.info(f"Processing scans dir : {path}")

    for entry in os.scandir(path):
        if entry.is_file():
            if _is_scans_file(entry.path):
                _do_inject_scans(ctx, entry.path)
        elif entry.is_dir() and ctx.recursive:
            _do_inject_dir(ctx, entry.path)


def _do_inject_all(ctx: BiContext, paths: List[str]):
    """Dispatch injection across a mixed list of file and directory paths.

    For each entry in *paths*: regular files are forwarded to
    :func:`_do_inject_scans`; directories are forwarded to
    :func:`_do_inject_dir` (which honours ``ctx.recursive``); anything else
    is logged as a warning and skipped.

    :param ctx: Processing context propagated to all subordinate calls.
    :type ctx: BiContext
    :param paths: Sequence of file or directory paths supplied by the caller.
    :type paths: List[str]
    """

    # iterate over paths and depending on whether it's a file or directory,
    # process accordingly
    for path in paths:
        if os.path.isfile(path):
            _do_inject_scans(ctx, path)
        elif os.path.isdir(path):
            _do_inject_dir(ctx, path)
        else:
            logger.warning(f"Skipping invalid path: {path}")


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

    Orchestrates loading of videos.tsv, discovery of ``*_scans.tsv`` files,
    per-scan matching, slicing, and injection.

    :param paths: Tuple of file or directory paths from the CLI ``PATHS`` argument.
    :type paths: tuple
    :param videos_tsv: Path to ``videos.tsv`` produced by ``video-audit``.
        Video file paths inside the TSV are resolved relative to this file's location.
    :type videos_tsv: str
    :param recursive: When ``True``, recurse into subdirectories when searching
        for ``*_scans.tsv`` files.
    :type recursive: bool
    :param buffer_before: Extra video to include before scan onset.
        Accepts seconds (e.g. ``'10'``) or ISO 8601 duration (e.g. ``'PT10S'``).
    :type buffer_before: str
    :param buffer_after: Extra video to include after scan end.
        Accepts seconds (e.g. ``'10'``) or ISO 8601 duration (e.g. ``'PT10S'``).
    :type buffer_after: str
    :param buffer_policy: ``'strict'`` to error when buffers exceed video
        boundaries; ``'flexible'`` to trim them instead.
    :type buffer_policy: str
    :param time_offset: Clock offset in seconds added to ``acq_time`` values
        after timezone normalisation.
    :type time_offset: float
    :param qr: QR timing refinement mode: ``'none'``, ``'auto'``,
        ``'embed-existing'``, or ``'parse'``.
    :type qr: str
    :param layout: Output placement layout: ``'nearby'`` or ``'top-stimuli'``.
    :type layout: str
    :param timezone: Timezone for ReproStim timestamps. Use ``'local'`` for
        the OS timezone or an IANA name (e.g. ``'America/New_York'``).
    :type timezone: str
    :param dry_run: When ``True``, resolve matches and print planned actions
        but skip ``split-video`` and all file writes.
    :type dry_run: bool
    :param verbose: When ``True``, emit verbose progress output.
    :type verbose: bool
    :param out_func: Callable used for user-facing output (e.g. ``click.echo``).
    :type out_func: Callable
    :returns: Exit code — ``0`` on success, non-zero on error.
    :rtype: int
    """
    ctx: BiContext = BiContext(dry_run=dry_run, recursive=recursive)

    _do_inject_all(ctx, paths)

    return 0
