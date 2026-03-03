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
from datetime import datetime, time, timedelta, timezone, tzinfo
from enum import Enum
from functools import lru_cache
from typing import Callable, List, Optional, Tuple
from zoneinfo import ZoneInfo

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
    time_offset: float = Field(
        default=0.0,
        description="Clock offset in seconds added to acq_time values after "
        "timezone normalisation to handle security functionality if any.",
    )
    qr: QrMode = Field(
        default=QrMode.NONE,
        description="QR code-based timing refinement mode. "
        "Only 'none' is currently implemented; all other modes raise "
        "NotImplementedError.",
    )
    buffer_before: str = Field(
        default="0",
        description="Extra video to include before scan onset. "
        "Accepts seconds (e.g. '10') or ISO 8601 duration (e.g. 'PT10S').",
    )
    buffer_after: str = Field(
        default="0",
        description="Extra video to include after scan end. "
        "Accepts seconds (e.g. '10') or ISO 8601 duration (e.g. 'PT10S').",
    )
    buffer_policy: str = Field(
        default="flexible",
        description="Policy for handling buffer overflow beyond video boundaries: "
        "'strict' to error, 'flexible' to trim.",
    )
    layout: LayoutMode = Field(
        default=LayoutMode.NEARBY,
        description="Output file placement layout within the BIDS dataset. "
        "'nearby': place output next to the NIfTI in the same datatype folder. "
        "'top-stimuli': place output under stimuli/ at the BIDS root, "
        "mirroring the subject/session/datatype hierarchy.",
    )
    reprostim_timezone: str = Field(
        default="local",
        description="Timezone name for naive ReproStim timestamps in videos.tsv. "
        "Use 'local' for the OS timezone or an IANA name (e.g. 'America/New_York'). "
        "Resolved to a tzinfo via reprostim_tz property (cached).",
    )
    bids_timezone: str = Field(
        default="local",
        description="Timezone name for naive BIDS acq_time values in _scans.tsv. "
        "Use 'local' for the OS timezone or an IANA name (e.g. 'America/New_York'). "
        "Resolved to a tzinfo via bids_tz property (cached).",
    )

    @property
    def reprostim_tz(self) -> tzinfo:
        """Resolved :class:`tzinfo` for :attr:`reprostim_timezone` (cached)."""
        return dt_resolve_tz(self.reprostim_timezone)

    @property
    def bids_tz(self) -> tzinfo:
        """Resolved :class:`tzinfo` for :attr:`bids_timezone` (cached)."""
        return dt_resolve_tz(self.bids_timezone)

    lock: bool = Field(
        default=True,
        description="When True (default), acquire the advisory file lock before "
        "reading videos.tsv. When False, skip the lock (dirty-read mode) — "
        "useful when the lock is owned by a different OS user.",
    )
    verbose: bool = Field(
        default=False,
        description="When True, emit verbose progress output.",
    )
    out_func: Optional[Callable] = Field(
        default=None,
        description="Callable used for user-facing output (e.g. click.echo). "
        "When None, output is suppressed.",
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
        times = [dt_time_to_sec(dt_parse_dicom_time(s)) for s in md.AcquisitionTime]
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
    time_offset: float = 0.0,
    reprostim_tz: Optional[tzinfo] = None,
    bids_tz: Optional[tzinfo] = None,
) -> Optional[Tuple[datetime, datetime]]:
    """Calculate scan start and end timestamps from a :class:`ScanRecord`.

    Parses :attr:`ScanRecord.acq_time` as the scan start datetime, applies
    timezone conversion from BIDS domain to ReproStim domain (when
    *reprostim_tz* and *bids_tz* are provided), optionally applies
    *time_offset*, then derives the end timestamp from
    :attr:`ScanRecord.duration_sec`.

    Both timestamps are returned as naive :class:`datetime.datetime` objects
    in the ReproStim timezone, matching the convention used in ``videos.tsv``.

    Returns ``None`` when :attr:`ScanRecord.duration_sec` is ``None``.

    :param record: Scan record with ``acq_time`` and ``duration_sec`` populated.
    :type record: ScanRecord
    :param time_offset: Clock offset in seconds added to the start timestamp.
        Defaults to ``0.0``.
    :type time_offset: float
    :param reprostim_tz: ReproStim capture machine timezone
        (from ``--reprostim-timezone``). When ``None``, no conversion is done.
    :type reprostim_tz: Optional[datetime.tzinfo]
    :param bids_tz: BIDS dataset timezone (from ``--bids-timezone``).
        When ``None``, no conversion is done.
    :type bids_tz: Optional[datetime.tzinfo]
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

    start_dt = dt_parse_bids(record.acq_time)

    if reprostim_tz is not None and bids_tz is not None:
        start_dt = dt_bids_to_reprostim(start_dt, bids_tz, reprostim_tz)

    if time_offset:
        start_dt += timedelta(seconds=time_offset)

    end_dt = start_dt + timedelta(seconds=record.duration_sec)
    return start_dt, end_dt


def _calc_media_suffix(va) -> Optional[MediaSuffix]:
    """Determine the BEP044 recording-type suffix from a video-audit record.

    Inspects ``video_res_detected`` and ``audio_sr`` fields of *va* per the
    decision table in the spec:

    +----------------------+----------------+---------------+
    | ``video_res_detected``| ``audio_sr``  | Suffix        |
    +======================+================+===============+
    | present              | present        | ``_audiovideo``|
    +----------------------+----------------+---------------+
    | present              | absent / ``n/a``| ``_video``   |
    +----------------------+----------------+---------------+
    | absent / ``n/a``     | present        | ``_audio``    |
    +----------------------+----------------+---------------+
    | absent / ``n/a``     | absent / ``n/a``| ``None``     |
    +----------------------+----------------+---------------+

    Returns ``None`` when neither stream is detected; the caller should skip
    the injection and log a warning.

    :param va: Video-audit record from ``videos.tsv``.
    :returns: Appropriate :class:`MediaSuffix`, or ``None`` to skip.
    :rtype: Optional[MediaSuffix]
    """
    has_video = bool(va.video_res_detected and va.video_res_detected != "n/a")
    has_audio = bool(va.audio_sr and va.audio_sr != "n/a")

    if has_video and has_audio:
        return MediaSuffix.AUDIOVIDEO
    elif has_video:
        return MediaSuffix.VIDEO
    elif has_audio:
        return MediaSuffix.AUDIO

    logger.warning(
        f"Cannot determine media suffix: no video or audio stream detected "
        f"in {va.name!r}"
    )
    return None


def _find_bids_root(scans_path: str) -> str:
    """Find the BIDS dataset root directory from a ``*_scans.tsv`` path.

    Walks upward from the directory containing *scans_path*, looking for a
    ``dataset_description.json`` file, which is required at the BIDS root.

    Falls back to the parent of the first ``sub-`` path component when the
    dataset description file is not found.

    :param scans_path: Absolute or relative path to a ``*_scans.tsv`` file.
    :type scans_path: str
    :returns: Absolute path to the BIDS dataset root.
    :rtype: str
    """
    scans_dir = os.path.dirname(os.path.abspath(scans_path))

    # Primary: walk upward looking for dataset_description.json
    current = scans_dir
    while True:
        if os.path.isfile(os.path.join(current, "dataset_description.json")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    # Fallback: parent of the first sub-XX component in the absolute path
    parts = os.path.abspath(scans_dir).split(os.sep)
    for i, part in enumerate(parts):
        if re.match(r"^sub-", part):
            return os.sep.join(parts[:i]) or os.sep

    logger.warning(
        f"Cannot determine BIDS root for {scans_path}; "
        f"using scans file parent directory as fallback."
    )
    return os.path.dirname(scans_dir)


def _calc_bids_output_stem(filename: str) -> Tuple[str, str]:
    """Derive the output filename stem by stripping the BIDS datatype suffix.

    Removes the ``.nii`` / ``.nii.gz`` extension, extracts any trailing
    ReproIn-style suffix (double-underscore convention, e.g. ``__dup-01``),
    and then strips the last BIDS suffix token (e.g. ``_bold``, ``_T1w``) —
    the trailing ``_[A-Za-z][A-Za-z0-9]*`` segment — so the caller can
    insert a recording-type suffix such as ``_recording-reprostim_audiovideo``
    before the reproin suffix.

    Examples::

        # Standard BIDS name — no reproin suffix
        _calc_bids_output_stem("func/sub-qa_ses-20250814_acq-faX77_bold.nii.gz")
        # → ("func/sub-qa_ses-20250814_acq-faX77", "")

        # ReproIn name with __dup-01 suffix
        _calc_bids_output_stem(
            "func/sub-qa_ses-20250814_task-rest_acq-p2_bold__dup-01.nii.gz"
        )
        # → ("func/sub-qa_ses-20250814_task-rest_acq-p2", "__dup-01")

    The caller assembles the final output path as::

        base_stem + "_recording-reprostim" + media_suffix + reproin_suffix + ".mkv"

    :param filename: Relative NIfTI path from the scan record, e.g.
        ``func/sub-qa_ses-20250814_acq-faX77_bold.nii.gz``.
    :type filename: str
    :returns: ``(base_stem, reproin_suffix)`` where *base_stem* is the path
        without the NIfTI extension, BIDS suffix, or reproin suffix, and
        *reproin_suffix* is the extracted double-underscore token (e.g.
        ``"__dup-01"``) or an empty string when none is present.
    :rtype: Tuple[str, str]
    """
    stem = re.sub(r"\.nii(\.gz)?$", "", filename)

    # Extract ReproIn-style suffix: double-underscore followed by non-whitespace
    # characters at the end of the stem (e.g. "__dup-01").
    reproin_suffix = ""
    m = re.search(r"(__\S+)$", stem)
    if m:
        reproin_suffix = m.group(1)
        stem = stem[: m.start()]

    # Strip the BIDS suffix token (e.g. _bold, _T1w).
    stem = re.sub(r"_[A-Za-z][A-Za-z0-9]*$", "", stem)

    return stem, reproin_suffix


def _call_split_video(
    ctx: BiContext,
    scans_path: str,
    record: ScanRecord,
    va,
    start_ts: datetime,
    end_ts: datetime,
) -> None:
    """Invoke split-video for a single matched video record.

    Resolves the input video path from the ``videos.tsv`` directory and
    derives the output path from the ``*_scans.tsv`` location and scan
    filename stem.  Respects ``ctx.dry_run`` — when set, logs the planned
    action without executing the split.

    :param ctx: Processing context with buffer, policy, and dry-run settings.
    :type ctx: BiContext
    :param scans_path: Absolute path to the ``*_scans.tsv`` file being processed.
    :type scans_path: str
    :param record: Scan record being injected.
    :type record: ScanRecord
    :param va: Matched video-audit record from ``videos.tsv``.
    :param start_ts: Scan start timestamp (after time-offset applied).
    :type start_ts: datetime
    :param end_ts: Scan end timestamp.
    :type end_ts: datetime
    """
    media_suffix = _calc_media_suffix(va)
    if media_suffix is None:
        logger.warning(
            f"Skipping injection: cannot determine media suffix ({record.filename})"
        )
        return

    videos_dir = os.path.dirname(os.path.abspath(ctx.videos_tsv))
    input_path = os.path.join(videos_dir, va.path)
    scans_dir = os.path.dirname(os.path.abspath(scans_path))
    base_stem, reproin_suffix = _calc_bids_output_stem(record.filename)
    output_name = (
        base_stem + f"_recording-reprostim{media_suffix.value}{reproin_suffix}.mkv"
    )

    if ctx.layout == LayoutMode.TOP_STIMULI:
        bids_root = _find_bids_root(scans_path)
        rel_session = os.path.relpath(scans_dir, bids_root)
        output_path = os.path.join(bids_root, "stimuli", rel_session, output_name)
    else:  # LayoutMode.NEARBY (default)
        output_path = os.path.join(scans_dir, output_name)

    sidecar_path = output_path[: -len(".mkv")] + ".json"

    logger.info(f"Input video path       : {input_path}")
    logger.info(f"Output video path      : {output_path}")
    logger.info(f"Sidecar JSON path      : {sidecar_path}")

    if ctx.dry_run:
        logger.info(
            f"Dry-run                : split-video"
            f" --video-audit-file {ctx.videos_tsv}"
            f" --buffer-before {ctx.buffer_before}"
            f" --buffer-after {ctx.buffer_after}"
            f" --buffer-policy {ctx.buffer_policy}"
            f" --sidecar-json {sidecar_path}"
            f" --start {start_ts.isoformat()}"
            f" --end {end_ts.isoformat()}"
            f" --lock {'yes' if ctx.lock else 'no'}"
            f" --input {input_path}"
            f" --output {output_path}"
        )
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    from reprostim.qr.split_video import do_main as split_video_main

    ret = split_video_main(
        input_path=input_path,
        output_path=output_path,
        start_time=start_ts.isoformat(),
        end_time=end_ts.isoformat(),
        buffer_before=ctx.buffer_before,
        buffer_after=ctx.buffer_after,
        buffer_policy=ctx.buffer_policy,
        sidecar_json=sidecar_path,
        video_audit_file=ctx.videos_tsv,
        lock=ctx.lock,
        verbose=ctx.verbose,
        out_func=ctx.out_func or print,
    )
    if ret != 0:
        logger.error(f"split-video failed with exit code {ret} ({record.filename})")
    else:
        logger.info(f"split-video completed successfully ({record.filename})")


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
        if ctx.qr != QrMode.NONE:
            raise NotImplementedError(
                f"QR mode '{ctx.qr.value}' is not implemented yet. "
                f"Only '{QrMode.NONE.value}' is currently supported."
            )
        scans: ScansModel = _parse_scans_model(path)
        for sr in scans.records:
            if re.search(ctx.match, sr.filename):
                logger.info(f"Processing scan record : {sr}")
                sr.metadata = _parse_scan_metadata(scans, sr)
                logger.debug(f"Scan metadata          : {sr.metadata}")
                sr.duration_sec = _calc_scan_duration_sec(sr)
                logger.info(f"Scan duration          : {sr.duration_sec} s")

                start_ts, end_ts = _calc_scan_start_end_ts(
                    sr, ctx.time_offset, ctx.reprostim_tz, ctx.bids_tz
                )
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
                        ctx.videos_tsv,
                        start_ts,
                        end_ts,
                        cached=True,
                        use_lock=ctx.lock,
                    )
                    logger.info(f"Matching video records : {len(va_records)}")
                    for va in va_records:
                        logger.info(f"                       : {va.name}")
                        logger.debug(f"                       : {va.model_dump()}")
                    # Note: only process when 1 record provided, when 0 skip and
                    # in case more than 1 records, log an error that multiple videos
                    # are not supported yet  and skip as well (ambiguous match)
                    n_va = len(va_records)
                    if n_va == 0:
                        logger.info("No matching video records found, skipping.")
                    elif n_va > 1:
                        logger.error(
                            f"Ambiguous match: {n_va} video records overlap "
                            f"the scan window. Multiple videos per scan are "
                            f"not yet supported; skipping."
                        )
                    else:
                        _call_split_video(
                            ctx, path, sr, va_records[0], start_ts, end_ts
                        )

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
# Datetime / Timezone Public API
####################################################################


@lru_cache(maxsize=32)
def dt_resolve_tz(name: str) -> tzinfo:
    """Resolve a timezone name string to a :class:`datetime.tzinfo` object.

    Results are cached via :func:`functools.lru_cache`, so repeated calls
    with the same *name* are free after the first resolution.

    :param name: ``'local'`` to use the OS system timezone, or any IANA
        timezone name (e.g. ``'America/New_York'``, ``'UTC'``).
    :type name: str
    :returns: Corresponding :class:`tzinfo` instance.
    :rtype: datetime.tzinfo
    :raises ZoneInfoNotFoundError: If *name* is not a recognised IANA timezone.
    """
    if name.lower() == "local":
        return datetime.now().astimezone().tzinfo
    return ZoneInfo(name)


def dt_tz_label(name: str) -> str:
    """Return the current UTC offset for a timezone name, e.g. ``UTC-05:00``.

    Resolves the timezone name via :func:`dt_resolve_tz` and formats the
    UTC offset as ``"UTC±HH:MM"``, e.g. ``"UTC-05:00"`` or ``"UTC+00:00"``.

    :param name: Timezone name accepted by :func:`dt_resolve_tz`.
    :type name: str
    :returns: UTC offset string.
    :rtype: str
    """
    tz = dt_resolve_tz(name)
    offset = datetime.now(tz).utcoffset()
    total_sec = int(offset.total_seconds())
    sign = "+" if total_sec >= 0 else "-"
    h, m = divmod(abs(total_sec), 3600)
    return f"UTC{sign}{h:02d}:{m // 60:02d}"


def dt_parse_dicom_time(value: str) -> time:
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


def dt_time_to_sec(t: time) -> float:
    """Convert a :class:`datetime.time` to total seconds since midnight.

    :param t: Time value to convert.
    :type t: datetime.time
    :returns: Total seconds since midnight, including microseconds as a
        fractional part.
    :rtype: float
    """
    return t.hour * 3600 + t.minute * 60 + t.second + t.microsecond / 1_000_000


def dt_parse_bids(s: str) -> datetime:
    """Parse a BIDS ``acq_time`` ISO 8601 string to a naive :class:`datetime`.

    Any UTC offset present in *s* is stripped so the returned object has no
    ``tzinfo`` attached, matching the naive-datetime convention used throughout
    this module.

    :param s: ISO 8601 datetime string, e.g. ``'2025-08-14T15:06:09.742500'``.
    :type s: str
    :returns: Naive :class:`datetime` (no ``tzinfo``).
    :rtype: datetime.datetime
    :raises ValueError: If *s* cannot be parsed as an ISO 8601 datetime.
    """
    return datetime.fromisoformat(s).replace(tzinfo=None)


def dt_convert(dt: datetime, tz_from: tzinfo, tz_to: tzinfo) -> datetime:
    """Convert a naive datetime from one timezone context to another.

    Attaches *tz_from* to *dt*, converts to *tz_to*, then strips ``tzinfo``
    to return a naive datetime.  This is the primitive that all higher-level
    helpers delegate to.

    :param dt: Naive source datetime (no ``tzinfo``).
    :type dt: datetime.datetime
    :param tz_from: Timezone the naive *dt* implicitly represents.
    :type tz_from: datetime.tzinfo
    :param tz_to: Target timezone to convert into.
    :type tz_to: datetime.tzinfo
    :returns: Naive datetime in *tz_to*.
    :rtype: datetime.datetime
    """
    return dt.replace(tzinfo=tz_from).astimezone(tz_to).replace(tzinfo=None)


def dt_reprostim_to_utc(dt: datetime, tz: tzinfo) -> datetime:
    """Convert a naive ReproStim datetime to a naive UTC datetime.

    :param dt: Naive ReproStim datetime from ``videos.tsv``.
    :type dt: datetime.datetime
    :param tz: Timezone the ReproStim capture machine was using.
    :type tz: datetime.tzinfo
    :returns: Naive UTC datetime.
    :rtype: datetime.datetime
    """
    return dt_convert(dt, tz, timezone.utc)


def dt_bids_to_utc(dt: datetime, tz: tzinfo) -> datetime:
    """Convert a naive BIDS datetime to a naive UTC datetime.

    :param dt: Naive BIDS ``acq_time`` datetime.
    :type dt: datetime.datetime
    :param tz: Timezone assumed for the BIDS timestamps.
    :type tz: datetime.tzinfo
    :returns: Naive UTC datetime.
    :rtype: datetime.datetime
    """
    return dt_convert(dt, tz, timezone.utc)


def dt_utc_to_reprostim(dt: datetime, tz: tzinfo) -> datetime:
    """Convert a naive UTC datetime to a naive ReproStim-domain datetime.

    :param dt: Naive UTC datetime.
    :type dt: datetime.datetime
    :param tz: Target timezone (ReproStim capture machine timezone).
    :type tz: datetime.tzinfo
    :returns: Naive datetime in *tz*.
    :rtype: datetime.datetime
    """
    return dt_convert(dt, timezone.utc, tz)


def dt_utc_to_bids(dt: datetime, tz: tzinfo) -> datetime:
    """Convert a naive UTC datetime to a naive BIDS-domain datetime.

    :param dt: Naive UTC datetime.
    :type dt: datetime.datetime
    :param tz: Target timezone (BIDS dataset timezone).
    :type tz: datetime.tzinfo
    :returns: Naive datetime in *tz*.
    :rtype: datetime.datetime
    """
    return dt_convert(dt, timezone.utc, tz)


def dt_reprostim_to_bids(
    dt: datetime, reprostim_tz: tzinfo, bids_tz: tzinfo
) -> datetime:
    """Convert a naive ReproStim datetime directly to a naive BIDS datetime.

    Routes through UTC internally:
    ``dt_utc_to_bids(dt_reprostim_to_utc(dt, reprostim_tz), bids_tz)``.

    :param dt: Naive ReproStim datetime.
    :type dt: datetime.datetime
    :param reprostim_tz: ReproStim capture machine timezone.
    :type reprostim_tz: datetime.tzinfo
    :param bids_tz: BIDS dataset timezone.
    :type bids_tz: datetime.tzinfo
    :returns: Naive datetime in the BIDS timezone.
    :rtype: datetime.datetime
    """
    return dt_utc_to_bids(dt_reprostim_to_utc(dt, reprostim_tz), bids_tz)


def dt_bids_to_reprostim(
    dt: datetime, bids_tz: tzinfo, reprostim_tz: tzinfo
) -> datetime:
    """Convert a naive BIDS datetime directly to a naive ReproStim datetime.

    Routes through UTC internally:
    ``dt_utc_to_reprostim(dt_bids_to_utc(dt, bids_tz), reprostim_tz)``.

    :param dt: Naive BIDS ``acq_time`` datetime.
    :type dt: datetime.datetime
    :param bids_tz: BIDS dataset timezone.
    :type bids_tz: datetime.tzinfo
    :param reprostim_tz: ReproStim capture machine timezone.
    :type reprostim_tz: datetime.tzinfo
    :returns: Naive datetime in the ReproStim timezone.
    :rtype: datetime.datetime
    """
    return dt_utc_to_reprostim(dt_bids_to_utc(dt, bids_tz), reprostim_tz)


####################################################################
# Public API
####################################################################


def do_main(
    paths: List[str],
    videos_tsv: str,
    recursive: bool,
    match: str,
    buffer_before: str,
    buffer_after: str,
    buffer_policy: str,
    time_offset: float,
    qr: str,
    layout: str,
    reprostim_timezone: str,
    bids_timezone: str,
    dry_run: bool,
    lock: bool,
    verbose: bool,
    out_func: Callable,
) -> int:
    """Main entry point for the bids-inject command.

    Orchestrates loading of videos.tsv, discovery of ``*_scans.tsv`` files,
    per-scan matching, slicing, and injection.

    :param paths: List of file or directory paths from the CLI ``PATHS`` argument.
    :type paths: List[str]
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
    :param reprostim_timezone: Timezone for naive ReproStim timestamps in
        ``videos.tsv``. Use ``'local'`` for the OS timezone or an IANA name
        (e.g. ``'America/New_York'``).
    :type reprostim_timezone: str
    :param bids_timezone: Timezone for naive BIDS ``acq_time`` values.
        Use ``'local'`` or an IANA name.
    :type bids_timezone: str
    :param dry_run: When ``True``, resolve matches and print planned actions
        but skip ``split-video`` and all file writes.
    :type dry_run: bool
    :param lock: When ``True`` (default), acquire the advisory file lock
        before reading ``videos.tsv``. When ``False``, skip the lock
        (dirty-read mode) — useful when the lock file is owned by a
        different OS user.
    :type lock: bool
    :param layout: Output file placement layout: ``'nearby'`` places the output
        next to the NIfTI in the same BIDS datatype folder; ``'top-stimuli'``
        places it under a ``stimuli/`` directory at the BIDS root, mirroring
        the subject/session/datatype hierarchy.
    :type layout: str
    :param verbose: When ``True``, emit verbose progress output.
    :type verbose: bool
    :param out_func: Callable used for user-facing output (e.g. ``click.echo``).
    :type out_func: Callable
    :returns: Exit code — ``0`` on success, non-zero on error.
    :rtype: int
    """
    ctx: BiContext = BiContext(
        dry_run=dry_run,
        recursive=recursive,
        match=match,
        videos_tsv=videos_tsv,
        time_offset=time_offset,
        qr=QrMode(qr),
        buffer_before=buffer_before,
        buffer_after=buffer_after,
        buffer_policy=buffer_policy,
        layout=LayoutMode(layout),
        reprostim_timezone=reprostim_timezone,
        bids_timezone=bids_timezone,
        lock=lock,
        verbose=verbose,
        out_func=out_func,
    )

    _do_inject_all(ctx, paths)

    return 0
