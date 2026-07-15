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

from reprostim.bids.media import BidsMediaInfo, parse_bids_media_info
from reprostim.bids.properties import bids_properties_from_ffprobe

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


def _error(ctx: BisContext, msg: str) -> None:
    """Log *msg* as an error and report it via ``ctx.out_func``, if set.

    Shared by every per-file processing function in this module as the
    single place a fatal-for-this-file error is reported, so logging and
    ``out_func`` reporting stay consistent. Returns nothing — callers
    decide their own control flow, typically ``_error(ctx, msg); return
    False``.

    :param ctx: Processing context (used for ``out_func``).
    :type ctx: BisContext
    :param msg: Human-readable error message.
    :type msg: str
    """
    logger.error(msg)
    if ctx.out_func:
        ctx.out_func(f"Error: {msg}")


def _verbose(ctx: BisContext, msg: str) -> None:
    """Log *msg* at debug level and, when ``ctx.verbose`` is set, also
    report it via ``ctx.out_func``.

    Mirrors :func:`_error` for non-fatal, verbose-only diagnostic output.

    :param ctx: Processing context (used for ``verbose``/``out_func``).
    :type ctx: BisContext
    :param msg: Human-readable message.
    :type msg: str
    """
    logger.debug(msg)
    if ctx.verbose and ctx.out_func:
        ctx.out_func(msg)


def _do_sidecar(ctx: BisContext, path: str) -> bool:
    """Extract BIDS media-file metadata for *path* and write/update its
    sidecar JSON.

    Basic implementation: extraction is purely ``ffprobe``-based (via
    :func:`bids_properties_from_ffprobe`) plus ``ctx.ext_props``
    (``--add`` overrides). ``ctx.videos_tsv`` cache lookup is not
    consulted yet — see spec Open Questions.

    :param ctx: Processing context (mode, conflict policy, ext_props, etc.)
    :type ctx: BisContext
    :param path: Path to the audio/video file.
    :type path: str
    :return: ``True`` on success (sidecar written, or dry-run computed
        cleanly); ``False`` if the file was skipped due to an error.
    :rtype: bool
    """
    logger.debug(f"_do_sidecar(path={path})")

    # TODO: check file exists and when not report error and processing error

    bmi: BidsMediaInfo = parse_bids_media_info(path)
    logger.debug(f"bmi: {bmi}")
    if not bmi.valid:
        errors = "; ".join(f"{e.code.value}: {e.message}" for e in bmi.errors)
        _error(ctx, f"{path}: invalid BIDS media file: {errors}")
        return False

    props: dict = bids_properties_from_ffprobe(path)
    logger.debug(f"bids_props_ffrobe: {props}")

    # --add overrides take priority over extracted fields.
    fields: Dict[str, Any] = dict(props)
    fields.update(ctx.ext_props)

    sidecar_path = os.path.splitext(path)[0] + ".json"

    existing: Dict[str, Any] = {}
    if ctx.mode == OverwriteMode.UPDATE and os.path.isfile(sidecar_path):
        try:
            with open(sidecar_path) as f:
                existing = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            _error(ctx, f"{sidecar_path}: failed to read existing sidecar: {e}")
            return False

    merged: Dict[str, Any] = dict(existing)
    for field, value in fields.items():
        current = existing.get(field)
        if current is None or current == "n/a" or current == value:
            merged[field] = value
            continue

        # Conflict: existing has a different, non-"n/a" value.
        if ctx.conflict_policy == ConflictPolicy.ERROR:
            _error(
                ctx,
                f"{path}: conflicting value for {field!r}: "
                f"existing={current!r}, new={value!r}",
            )
            return False
        logger.warning(f"{path}: overwriting {field!r}: {current!r} -> {value!r}")
        _verbose(
            ctx, f"Warning: {path}: overwriting {field!r}: {current!r} -> {value!r}"
        )
        merged[field] = value

    if ctx.dry_run:
        if ctx.out_func:
            ctx.out_func(f"[DRY-RUN] {path} -> {sidecar_path}: {merged}")
        return True

    try:
        with open(sidecar_path, "w") as f:
            json.dump(merged, f, indent=2)
    except OSError as e:
        _error(ctx, f"{sidecar_path}: failed to write sidecar: {e}")
        return False

    _verbose(ctx, f"{path} -> {sidecar_path}: wrote {len(merged)} fields")

    return True


def _do_sidecar_all(ctx: BisContext, files: List[str]) -> int:
    """Process every path in *files*, writing/updating its sidecar.

    :param ctx: Processing context.
    :type ctx: BisContext
    :param files: Audio/video file paths to process.
    :type files: List[str]
    :return: Number of files that errored (invalid path, or a failure
        reported by :func:`_do_sidecar`).
    :rtype: int
    """
    errors = 0
    for path in files:
        if os.path.isfile(path):
            if not _do_sidecar(ctx, path):
                errors += 1
        else:
            _error(ctx, f"Skipping invalid path: {path}")
            errors += 1
    return errors


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

    For each file in ``files``, extracts BIDS media-file metadata via
    ``ffprobe`` (see :func:`_do_sidecar`), merges in ``add`` overrides, and
    writes/updates the corresponding ``.json`` sidecar according to ``mode``
    and ``existing_different``. ``videos`` (``videos.tsv`` cache lookup) is
    accepted but **not yet consulted** — extraction is ``ffprobe``-only for
    now; see .ai/spec-bids-inject-sidecar.md Open Questions.

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
        logger.debug(f"ext_props={ext_props}")
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
    error_count = _do_sidecar_all(ctx, files)

    n = len(files)
    prefix = "[DRY-RUN] " if dry_run else ""
    summary_line = (
        f"{prefix}{n} processed, {n - error_count} written, {error_count} errors"
    )
    logger.debug(summary_line)
    if out_func:
        out_func(summary_line)

    return 1 if error_count > 0 else 0
