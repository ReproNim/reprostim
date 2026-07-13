# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
Core logic for bids-inject-sidecar: extract BIDS media-file metadata from
audio/video files and write or update their ``.json`` sidecars.
"""

import json
import logging
import os
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

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
    videos_tsv: Optional[str] = Field(
        default=None,
        description="Optional path to videos.tsv used to look up cached "
        "fields instead of re-running ffprobe.",
    )
    dry_run: bool = Field(
        default=False,
        description="When True, compute but do not write any sidecar.",
    )
    verbose: bool = Field(
        default=False,
        description="When True, emit verbose per-field extraction/merge/conflict "
        "output.",
    )
    out_func: Optional[Callable] = Field(
        default=None,
        description="Callable used for user-facing output (e.g. click.echo). "
        "When None, output is suppressed.",
    )
    ext_props: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extra BIDS sidecar properties parsed from --add "
        "META=VALUE (or bare JSON object) values; see _parse_ext_props.",
    )


def _parse_ext_props(add_meta: List[str]) -> Dict[str, Any]:
    """Parse ``--add`` values into a dict of extra BIDS sidecar properties.

    Each entry in *add_meta* is one of:

    - A bare JSON object string, e.g. ``'{"AudioCodec": "aac",
      "AudioSampleRate": 48000}'``.
      Its top-level keys are treated as property names and merged directly into
      the result (a later entry's keys win over an earlier one's on conflict).
    - A ``META=VALUE`` pair, e.g. ``'AudioCodec=aac'``. If ``VALUE`` itself parses
      as JSON (e.g. ``'ExtraInfo={"key": "val"}'``), the parsed JSON value
      (dict/list/number/bool/null) is used as the property value; otherwise
      ``VALUE`` is stored verbatim as a string.

    :param add_meta: Raw values from repeated ``--add`` options.
    :type add_meta: List[str]
    :return: Property name -> value mapping.
    :rtype: Dict[str, Any]
    :raises ValueError: If an entry is neither a JSON object nor a
        ``META=VALUE`` pair with a non-empty ``META``.
    """
    props: Dict[str, Any] = {}
    for entry in add_meta:
        try:
            parsed = json.loads(entry)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            props.update(parsed)
            continue

        if "=" not in entry:
            raise ValueError(
                f"Invalid --add value {entry!r}: expected META=VALUE or a JSON object"
            )
        meta, _, value_str = entry.partition("=")
        meta = meta.strip()
        if not meta:
            raise ValueError(f"Invalid --add value {entry!r}: empty META name")

        try:
            value: Any = json.loads(value_str)
        except json.JSONDecodeError:
            value = value_str
        props[meta] = value

    return props


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
    :param add_meta: Raw values from repeated ``--add`` options — each either a
        ``META=VALUE`` pair or a bare JSON object string. See
        :func:`_parse_ext_props`.
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

    try:
        ext_props = _parse_ext_props(add_meta)
    except ValueError as e:
        logger.error(str(e))
        if out_func:
            out_func(f"Error: {e}")
        return 1

    ctx: BisContext = BisContext(
        mode=OverwriteMode(mode),
        conflict_policy=ConflictPolicy(existing_different),
        videos_tsv=videos,
        dry_run=dry_run,
        verbose=verbose,
        out_func=out_func,
        ext_props=ext_props,
    )
    _do_sidecar_all(ctx, files)

    return 0
