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
import json
import logging
import os
import re
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Callable, List, Optional, Tuple

from pydantic import BaseModel, Field

from reprostim.qr.video_audit import find_video_audit_by_timerange

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
    match: str = Field(
        default=".*",
        description="Regex pattern matched against ScanRecord.filename, "
        "only matching records are processed",
    )
    videos_tsv: Optional[str] = Field(
        default=None,
        description="Optional path to videos.tsv audit file used to look up "
        "matching video records by time range",
    )


class ScanMetadata(BaseModel):
    """Duration-relevant fields from a BIDS JSON sidecar file.

    Only the four fields required for scan-duration computation are promoted to
    typed attributes; every other key present in the JSON sidecar is stored
    verbatim in :attr:`extra`.

    Duration is resolved in priority order (see spec):

    1. ``FrameAcquisitionDuration`` (ms) — most reliable when present.
    2. ``AcquisitionTime`` array — ``(last - first + TR)`` seconds where
       ``TR = AcquisitionTime[1] - AcquisitionTime[0]``.
    3. ``RepetitionTime`` (s) × ``NumberOfVolumes``.
    """

    FrameAcquisitionDuration: Optional[float] = Field(
        default=None,
        description="Total frame acquisition duration in milliseconds (DICOM tag).",
    )
    AcquisitionTime: Optional[List[str]] = Field(
        default=None,
        description="Per-volume acquisition times in seconds since midnight.",
    )
    RepetitionTime: Optional[float] = Field(
        default=None,
        description="Repetition time (TR) in seconds.",
    )
    NumberOfVolumes: Optional[int] = Field(
        default=None,
        description="Number of volumes; may come from NIfTI header or JSON sidecar.",
    )
    extra: dict = Field(
        default_factory=dict,
        repr=False,
        description="All remaining sidecar keys not used for duration computation.",
    )


class ScanRecord(BaseModel):
    """A single row from a BIDS _scans.tsv file with optionally expanded metadata."""

    filename: str = Field(
        ..., description="Relative path to NIfTI within subject/session dir"
    )
    acq_time: str = Field(..., description="ISO 8601 acquisition start datetime")
    extra: dict = Field(
        default_factory=dict,
        description="All remaining columns from the TSV row as key/value pairs",
    )
    metadata: Optional[ScanMetadata] = Field(
        default=None,
        description="Parsed BIDS JSON sidecar metadata for this scan record.",
    )
    duration_sec: Optional[float] = Field(
        default=None,
        description="Scan duration in seconds, computed from sidecar metadata.",
    )


class ScansModel(BaseModel):
    """Parsed representation of a single BIDS ``*_scans.tsv`` file."""

    path: str = Field(
        ..., description="Absolute or relative path to the ``*_scans.tsv`` file"
    )
    records: List[ScanRecord] = Field(
        default_factory=list,
        description="Ordered list of scan records parsed from the file",
    )


####################################################################
# Internal API
####################################################################


def parse_dicom_time(value: str) -> time:
    """Parse a DICOM TM (Time) string into a :class:`datetime.time` object.

    Accepts the DICOM TM format ``HHMMSS.FFFFFF`` where:

    - ``HH`` — hours, 00–23
    - ``MM`` — minutes, 00–59
    - ``SS`` — seconds, 00–60 (60 permitted for leap seconds; clamped to 59
      for :class:`datetime.time` compatibility)
    - ``.FFFFFF`` — optional fractional seconds (1–6 digits, right-padded
      with zeros to form microseconds)

    :param value: DICOM TM string, e.g. ``'151953.397500'`` or ``'151953'``.
    :type value: str
    :returns: Corresponding :class:`datetime.time` instance.
    :rtype: datetime.time
    :raises ValueError: If *value* does not match the expected DICOM TM format.
    """
    m = re.fullmatch(r"(\d{2})(\d{2})(\d{2})(?:\.(\d{1,6}))?", value.strip())
    if not m:
        raise ValueError(f"Invalid DICOM TM value: {value!r}")
    hh, mm, ss = int(m.group(1)), int(m.group(2)), int(m.group(3))
    frac = m.group(4)
    microsecond = int(frac.ljust(6, "0")) if frac else 0
    # datetime.time does not support leap second 60; clamp to 59
    if ss == 60:
        ss = 59
    return time(hh, mm, ss, microsecond)


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


def _parse_scan_metadata(
    model: ScansModel, record: ScanRecord
) -> Optional[ScanMetadata]:
    """Parse BIDS JSON sidecar metadata for a given scan record.

    Locates the JSON sidecar by replacing the NIfTI extension (``.nii.gz``
    or ``.nii``) with ``.json`` in :attr:`ScanRecord.filename`, resolved
    relative to the directory containing the ``*_scans.tsv`` file.

    The four duration-relevant keys (``FrameAcquisitionDuration``,
    ``AcquisitionTime``, ``RepetitionTime``, ``NumberOfVolumes``) are
    mapped to typed fields on :class:`ScanMetadata`; all remaining keys are
    stored verbatim in :attr:`ScanMetadata.extra`.

    :param model: Parent :class:`ScansModel` whose ``path`` is used to
        resolve the sidecar location.
    :type model: ScansModel
    :param record: Scan record whose JSON sidecar to parse.
    :type record: ScanRecord
    :returns: Parsed :class:`ScanMetadata` when the sidecar exists and can
        be read, ``None`` otherwise.
    :rtype: Optional[ScanMetadata]
    """
    nifti_name = record.filename
    if nifti_name.endswith(".nii.gz"):
        json_name = nifti_name[: -len(".nii.gz")] + ".json"
    elif nifti_name.endswith(".nii"):
        json_name = nifti_name[: -len(".nii")] + ".json"
    else:
        logger.warning(f"Cannot derive JSON sidecar path from: {nifti_name}")
        return None

    scans_dir = os.path.dirname(os.path.abspath(model.path))
    json_path = os.path.join(scans_dir, json_name)

    if not os.path.isfile(json_path):
        logger.warning(f"JSON sidecar not found: {json_path}")
        return None

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # Per-volume AcquisitionTime array lives under time.samples, not at the
    # top level (which holds only the first volume's time as a plain string).
    acq_time_list: Optional[List[str]] = (
        data.get("time", {}).get("samples", {}).get("AcquisitionTime")
    )

    known_keys = {
        "FrameAcquisitionDuration",
        "RepetitionTime",
        "NumberOfVolumes",
    }
    return ScanMetadata(
        FrameAcquisitionDuration=data.get("FrameAcquisitionDuration"),
        AcquisitionTime=acq_time_list,
        RepetitionTime=data.get("RepetitionTime"),
        NumberOfVolumes=data.get("NumberOfVolumes"),
        extra={k: v for k, v in data.items() if k not in known_keys},
    )


def _parse_scans_model(path: str) -> ScansModel:
    """Parse a ``*_scans.tsv`` file and return a :class:`ScansData` instance.

    Reads a tab-separated BIDS scans file. The columns ``filename`` and
    ``acq_time`` are required; ``operator`` and ``randstr`` are read when
    present and left as ``None`` otherwise.

    :param path: Absolute or relative path to a ``*_scans.tsv`` file.
    :type path: str
    :returns: Parsed scans data containing the file path and one
        :class:`ScanRecord` per data row.
    :rtype: ScansModel
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
                    extra={
                        k: v
                        for k, v in row.items()
                        if k not in ("filename", "acq_time")
                    },
                )
            )
    logger.debug(f"Parsed {len(records)} scan records from: {path}")
    return ScansModel(path=path, records=records)


def time_to_sec(t: time) -> float:
    """Convert a :class:`datetime.time` to total seconds since midnight.

    :param t: Time value to convert.
    :type t: datetime.time
    :returns: Total seconds since midnight, including microseconds as a
        fractional part.
    :rtype: float
    """
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000


def _calc_scan_duration_sec(record: ScanRecord) -> Optional[float]:
    """Calculate scan duration in seconds from a :class:`ScanRecord`'s metadata.

    Resolution follows the priority order defined in the spec:

    1. ``FrameAcquisitionDuration`` (ms) — most reliable; divided by 1000.
    2. ``AcquisitionTime`` array of DICOM TM strings —
       ``(t_last − t_first) + TR`` where ``TR = t_times[1] − t_times[0]``.
       Requires at least two elements.
    3. ``RepetitionTime`` (s) × ``NumberOfVolumes``.

    Returns ``None`` and logs a warning when none of the three sources are
    available or sufficient.

    :param record: Scan record with populated :attr:`ScanRecord.metadata`.
    :type record: ScanRecord
    :returns: Scan duration in seconds, or ``None`` if it cannot be determined.
    :rtype: Optional[float]
    """
    md = record.metadata
    if md is None:
        logger.warning(f"No metadata available for: {record.filename}")
        return None

    # Priority 1: FrameAcquisitionDuration (ms → seconds)
    if md.FrameAcquisitionDuration is not None:
        duration = md.FrameAcquisitionDuration / 1000.0
        logger.debug(
            f"Duration from FrameAcquisitionDuration: {duration:.3f} s"
            f" ({record.filename})"
        )
        return duration

    # Priority 2: AcquisitionTime array — (t_last - t_first) + TR
    if md.AcquisitionTime is not None and len(md.AcquisitionTime) >= 2:
        times = [time_to_sec(parse_dicom_time(s)) for s in md.AcquisitionTime]
        tr = times[1] - times[0]
        duration = times[-1] - times[0] + tr
        logger.debug(
            f"Duration from AcquisitionTime array: {duration:.3f} s"
            f" (TR={tr:.3f} s, {record.filename})"
        )
        return duration

    # Priority 3: RepetitionTime × NumberOfVolumes
    if md.RepetitionTime is not None and md.NumberOfVolumes is not None:
        duration = md.RepetitionTime * md.NumberOfVolumes
        logger.debug(
            f"Duration from RepetitionTime × NumberOfVolumes: {duration:.3f} s"
            f" ({record.filename})"
        )
        return duration

    logger.warning(f"Cannot determine scan duration for: {record.filename}")
    return None


def _calc_scan_start_end_ts(
    record: ScanRecord,
) -> Optional[Tuple[datetime, datetime]]:
    """Calculate scan start and end timestamps from a :class:`ScanRecord`.

    Parses :attr:`ScanRecord.acq_time` as the scan start datetime and adds
    :attr:`ScanRecord.duration_sec` to derive the end datetime.  Both values
    are returned as **timezone-neutral** (naive) :class:`datetime.datetime`
    objects — any UTC offset present in ``acq_time`` is stripped before
    returning, matching the ReproStim convention of naive local-time datetimes.

    Returns ``None`` when :attr:`ScanRecord.duration_sec` is ``None``
    (i.e. duration could not be determined).

    :param record: Scan record with ``acq_time`` and ``duration_sec`` populated.
    :type record: ScanRecord
    :returns: ``(start_ts, end_ts)`` as naive :class:`datetime.datetime` objects,
        or ``None`` if the duration is unavailable.
    :rtype: Optional[Tuple[datetime, datetime]]
    """
    if record.duration_sec is None:
        logger.warning(
            f"Cannot compute scan timestamps: duration_sec is None"
            f" ({record.filename})"
        )
        return None

    start_dt = datetime.fromisoformat(record.acq_time).replace(tzinfo=None)
    end_dt = start_dt + timedelta(seconds=record.duration_sec)

    # Note: in future convert time from BIDS data set to reprostim time zone
    # (e.g. local) before returning, to match the ReproStim convention of
    # naive local-time datetimes
    return start_dt, end_dt


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
        logger.info(f"Processing scans file  : {path}")
        scans: ScansModel = _parse_scans_model(path)
        for sr in scans.records:
            if re.search(ctx.match, sr.filename):
                logger.info(f"Processing scan record : {sr}")
                sr.metadata = _parse_scan_metadata(scans, sr)
                logger.debug(f"Scan metadata          : {sr.metadata}")
                sr.duration_sec = _calc_scan_duration_sec(sr)
                logger.info(f"Scan duration          : {sr.duration_sec} s")

                start_ts, end_ts = _calc_scan_start_end_ts(sr)
                logger.info(
                    f"Scan start_ts          : "
                    f"{start_ts.isoformat() if start_ts else None}"
                )
                logger.info(
                    f"Scan end_ts            : {end_ts.isoformat() if end_ts else None}"
                )

                # find matching video records in videos.tsv if any
                if ctx.videos_tsv and start_ts and end_ts:
                    va_records = find_video_audit_by_timerange(
                        ctx.videos_tsv, start_ts, end_ts, cached=True
                    )
                    logger.info(f"Matching video records : {len(va_records)}")
                    for va in va_records:
                        logger.debug(f"  video record         : {va.name}")
                        logger.debug(f"                       : {va.model_dump()}")

            else:
                logger.debug(f"Skipping scan record (no match): {sr.filename}")
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

    logger.info(f"Processing scans dir   : {path}")

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
    match: str,
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
    :param match: Regular expression matched against the ``filename`` field of
        each :class:`ScanRecord`. Only matching records are processed; others
        are skipped. Default ``'.*'`` matches every record.
    :type match: str
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
    ctx: BiContext = BiContext(
        dry_run=dry_run, recursive=recursive, match=match, videos_tsv=videos_tsv
    )

    _do_inject_all(ctx, paths)

    return 0
