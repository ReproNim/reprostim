# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
API to analyze video files recorded by reprostim-videocapture, along with
their corresponding log files and QR/audio metadata. It extracts key
information about each recording and produces a summary table (videos.tsv)
suitable for quality control, sharing, and further analysis.
"""

import csv
import getpass
import json
import fnmatch
import logging
import os
import re
import socket
import subprocess
import traceback
import tempfile
from datetime import datetime
from enum import Enum
from time import time
from typing import Dict, Generator, List, Set, Optional
from filelock import FileLock

from pydantic import BaseModel

from reprostim.qr.qr_parse import (
    InfoSummary,
    ParseSummary,
    VideoTimeInfo,
    do_info_file,
    do_parse,
)

# initialize the logger
# Note: all logs out to stderr
logger = logging.getLogger(__name__)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.debug(f"name={__name__}")


# Precalculated globals

# User@Host string
UPDATED_BY = f"{getpass.getuser()}@{socket.gethostname()}"

# Global REPROSTIM-METADATA-JSON regex pattern
JSON_PATTERN = re.compile(r"REPROSTIM-METADATA-JSON: (.*) :REPROSTIM-METADATA-JSON")


# NB: move in future to audio package or tool?
class AudioInfo(BaseModel):
    """Audio information extracted from the video file."""

    bits_per_sample: Optional[int] = None  # Bits per sample
    channels: Optional[int] = None  # Number of audio channels
    codec: Optional[str] = None  # Audio codec used
    duration_sec: Optional[float] = None  # Duration in seconds
    sample_rate: Optional[int] = None  # Sample rate in Hz


class VaMode(str, Enum):
    """Video audit processing mode constants."""

    FULL = "full"
    """Process all files, overwrite existing records in TSV
    completely."""
    INCREMENTAL = "incremental"
    """Process only new files not present in existing TSV and
    keep existing records."""
    FORCE = "force"
    """Force redo/overwrite specified records in TSV"""
    RERUN_FOR_NA = "rerun-for-na"
    """Process only records with 'n/a' values in existing TSV
    in columns that are usually filled by external tools.
    Intended for run external slow tools like detect-noscreen 
    or qr-parser."""
    RESET_TO_NA = "reset-to-na"
    """Reset specified columns to 'n/a' in existing TSV.
    Intended to clear results of external tools like
    detect-noscreen or qr-parser to rerun them from scratch."""


class VaRecord(BaseModel):
    """A single record in the videos.tsv audit summary."""

    # File info
    path: str = "n/a"  # Path to the .mkv video file
    present: bool = False  # Whether the file is present
    complete: bool = False  # Whether the recording was completed
    # and end timestamp is present
    name: str = "n/a"  # Short base name of the file

    # Start and end timestamps
    start_date: str = "n/a"
    start_time: str = "n/a"
    end_date: str = "n/a"
    end_time: str = "n/a"

    # Video detection info
    video_res_detected: str = "n/a"  # e.g., "1920x1080"
    video_fps_detected: str = "n/a"
    video_dur_detected: str = "n/a"  # video duration in seconds
    #                                 based on timestamps
    video_res_recorded: str = "n/a"  # e.g., "1920x1080"
    video_fps_recorded: str = "n/a"
    video_dur_recorded: str = "n/a"  # video duration in seconds
    video_size_mb: str = "n/a"  # size of the video file in MB
    video_rate_mbpm: str = "n/a"  # bitrate in mbpm

    # Audio info
    audio_sr: str = "n/a"  # sample rate
    audio_dur: str = "n/a"  # audio stream duration in seconds

    # Duration
    duration: str = "n/a"  # seconds
    duration_h: str = "n/a"  # human readable, e.g., "01:23:45"

    # Analysis info
    no_signal_frames: str = "n/a"  # number of frames with no signal, or %
    qr_records_number: str = "n/a"  # number of detected QR codes

    # Coherence check
    file_log_coherent: bool = False  # whether video/audio info matches extracted

    # Update info
    updated_on: str = "n/a"
    updated_by: str = "n/a"


class VaSource(str, Enum):
    """Video audit source constants."""

    ALL = "all"
    """Run all available audit sources."""
    INTERNAL = "internal"
    """Basic and default behaviour to process quickly video files 
    using only mediainfo and logs metadata."""
    NOSIGNAL = "nosignal"
    """Process video files to detect no-signal frames. This is slow process and
    can take some time depending on the video length."""
    QR = "qr"
    """Process video files to extract QR codes metadata. This is very slow 
    process and time is almost the same as video duration at this moment."""


class VaContext(BaseModel):
    """Context for video audit processing."""

    c_internal: Optional[int] = 0
    """Count of files processed with INTERNAL source"""
    c_nosignal: Optional[int] = 0
    """Count of files processed with NOSIGNAL source"""
    c_qr: Optional[int] = 0
    """Count of files processed with QR source"""
    log_level: Optional[str] = None
    """Logging level to be used in external tool, one of DEBUG, 
    INFO, WARNING, ERROR, CRITICAL (default: None)"""
    max_counter: Optional[int] = -1
    """Max number of records to process or -1 for 
    unlimited (default: -1)
    """
    mode: Optional[VaMode] = VaMode.INCREMENTAL
    """Operation mode, one of VaMode values (default: INCREMENTAL)
    """
    nosignal_data_dir: Optional[str] = "derivatives/nosignal"
    """Directory to store nosignal output data in JSON format.
    """
    nosignal_log_dir: Optional[str] = "logs/nosignal"
    """Directory to store nosignal logs.
    """
    nosignal_opts: Optional[List] = ["--number-of-checks", "100",
                                     "--truncated", "fixup",
                                     "--invalid-timing", "fixup",
                                     "--threshold", "1.01",]
    """Additional options to pass to detect-noscreen tool.
    """
    path_mask: Optional[str] = None
    """Optional path mask to filter video files based on their paths.
    """
    qr_data_dir: Optional[str] = "derivatives/qr"
    """Directory to store qr-parse output data in JSON format.
    """
    qr_log_dir: Optional[str] = "logs/qr"
    """Directory to store qr-parse logs.
    """
    qr_opts: Optional[List] = []
    """Additional options to pass to qr-parse tool if any.
    """
    recursive: Optional[bool] = False
    """Whether to scan directories recursively. Default: False
    """
    skip_names: Optional[set] = None
    """Optional set of file base names to skip (for incremental mode)
    """
    source: Optional[Set[VaSource]] = { VaSource.INTERNAL }
    """One of VaSource values to specify audit source (default: INTERNAL)
    """
    updated_paths: Optional[set] = set()
    """Optional set of updated record paths
    """


def check_coherent(vr: VaRecord) -> bool:
    """Check if the video record is coherent."""
    if not vr.present:
        logger.debug("check_coherent: File not present")
        return False
    if not vr.complete:
        logger.debug("check_coherent: File not complete")
        return False
    if vr.start_date == "n/a" or vr.start_time == "n/a":
        logger.debug("check_coherent: No start date/time")
        return False
    if vr.end_date == "n/a" or vr.end_time == "n/a":
        logger.debug("check_coherent: No end date/time")
        return False
    if vr.video_res_detected == "n/a" or vr.video_fps_detected == "n/a":
        logger.debug("check_coherent: No video res/fps detected")
        return False
    if vr.video_res_recorded == "n/a" or vr.video_fps_recorded == "n/a":
        logger.debug("check_coherent: No video res/fps recorded")
        return False
    if vr.duration == "n/a" or vr.duration_h == "n/a":
        logger.debug("check_coherent: No duration available")
        return False
    if vr.video_res_detected != vr.video_res_recorded:
        logger.debug(
            f"check_coherent: Video res mismatch: "
            f"detected={vr.video_res_detected}, "
            f"recorded={vr.video_res_recorded}"
        )
        return False
    if int(float(vr.video_fps_detected)) != int(float(vr.video_fps_recorded)):
        logger.debug(
            f"check_coherent: Video fps mismatch: "
            f"detected={vr.video_fps_detected}, "
            f"recorded={vr.video_fps_recorded}"
        )
        return False

    return True


def check_ffprobe():
    """Check if ffprobe is installed and available in PATH.
    :return: True if ffprobe is available, False otherwise
    :rtype: bool
    """
    try:
        # Try running `ffprobe -version` to see if it's installed
        subprocess.run(
            ["ffprobe", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        logger.debug("ffprobe is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Error: ffprobe is not installed")
        return False


def format_date(dt: datetime) -> str:
    """
    Extract date from datetime as 'YYYY-MM-DD' string.
    Ignores timezone.

    :param dt: datetime object
    :type dt: datetime

    :return: formatted date string
    :rtype: str
    """
    if dt is None:
        return "n/a"
    return dt.date().isoformat()


def format_duration(duration_sec: float) -> str:
    """
    Convert duration in seconds to human-readable string HH:MM:SS
    or HH:MM:SS.mmm. If duration_sec is None, return "n/a"

    :param duration_sec: Duration in seconds
    :type duration_sec: float

    :return: Formatted duration string
    :rtype: str
    """
    if duration_sec is None:
        return "n/a"

    hours = int(duration_sec // 3600)
    minutes = int((duration_sec % 3600) // 60)
    seconds = duration_sec % 60
    # Include milliseconds if needed
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"  # HH:MM:SS.mmm


def format_time(dt: datetime) -> str:
    """
    Extract time from datetime as 'HH:MM:SS.mmm' string.
    Ignores timezone.

    :param dt: datetime object
    :type dt: datetime

    :return: formatted time string
    :rtype: str
    """
    if dt is None:
        return "n/a"
    # Convert microseconds to milliseconds
    ms = dt.microsecond // 1000
    return f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}.{ms:03d}"


def format_tts(t: float) -> str:
    """Converts a time.time() timestamp into an ISO 8601 formatted string
    with local timezone.

    This function takes a timestamp in seconds and converts it into a
    datetime object with local timezone.

    :param t: The timestamp to be converted in seconds.
    :type t: float

    :return: The ISO 8601 formatted string with local timezone.
    :rtype: str
    """
    dt: datetime = datetime.fromtimestamp(t)
    return f"{format_date(dt)} {format_time(dt)}"


def iter_metadata_json(log_path: str) -> Generator[Dict, None, None]:
    """
    Iterate over all REPROSTIM-METADATA-JSON lines in the log file.
    Yields parsed JSON dictionaries.

    :param log_path: Path to the log file
    :type log_path: str

    :return: Generator of parsed JSON dictionaries
    :rtype: Generator[Dict, None, None]
    """
    if not os.path.exists(log_path):
        logger.error(f"Log file does not exist: {log_path}")
        return  # file missing, generator yields nothing

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            match = JSON_PATTERN.search(line)
            if match:
                try:
                    data = json.loads(match.group(1))
                    yield data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON in line: {line}")
                    continue


def find_metadata_json(path: str, key: str, value) -> Optional[Dict]:
    """Find the first metadata JSON entry with a specific key-value pair.

    :param path: Path to the log file
    :type path: str

    :param key: Key to search for
    :type key: str

    :param value: Value to match
    :type value: Any

    :return: The first matching dictionary or None if not found
    :rtype: Optional[Dict]
    """
    return next(
        (msg for msg in iter_metadata_json(path) if msg.get(key) == value), None
    )


# NB: move in future to audio package or tool?
def get_audio_info_ffprobe(path: str) -> AudioInfo:
    """Extract audio information from the video file using ffprobe.

    :param path: Path to the video file(.mkv, .mp4, .avi)
    :type path: str

    :return: AudioInfo object with extracted audio information
    :rtype: AudioInfo
    """

    logger.debug(f"get_audio_info: {path}")
    ai: AudioInfo = AudioInfo()

    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",  # suppress logs
            "-print_format",
            "json",  # JSON output
            "-show_streams",  # streams
            "-select_streams",
            "a",  # filter all audio streams
            path,
        ]
        # cmd = ["ffprobe", "-h"]
        logger.debug(f"run: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # logger.debug(f"ffprobe -> {result.stdout}")
        o = json.loads(result.stdout)
        logger.debug(f"ffprobe output: {o}")

        streams = o.get("streams", [])
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

        if audio_streams:
            stream = audio_streams[
                0
            ]  # take first audio stream (or iterate if multiple)

            bps = stream.get("bits_per_sample")
            if bps is not None and bps != 0:
                ai.bits_per_sample = bps
            ai.channels = stream.get("channels")
            ai.codec = stream.get("codec_name")
            ai.sample_rate = (
                int(stream["sample_rate"]) if "sample_rate" in stream else None
            )

            # duration is usually in tags, but sometimes in stream
            if "tags" in stream and "DURATION" in stream["tags"]:
                # Example: "00:00:17.150000000"
                h, m, s = stream["tags"]["DURATION"].split(":")
                ai.duration_sec = int(h) * 3600 + int(m) * 60 + float(s)
            elif "duration" in stream:
                ai.duration_sec = float(stream["duration"])

    except FileNotFoundError:
        logger.error("ffprobe is not installed or not in PATH")
    except subprocess.CalledProcessError as e:
        logger.error(f"ffprobe error: {e} {e.stdout} {e.stderr}")

    return ai


def _save_tsv(records: List[VaRecord], path_out: str):
    fields = list(VaRecord.model_fields.keys())
    with open(path_out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for r in records:
            writer.writerow(r.model_dump())


def _load_tsv(path_in: str) -> List[VaRecord]:
    records = []
    with open(path_in, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            records.append(VaRecord(**row))
    return records


def _merge_recs(ctx: VaContext,
               recs0: List[VaRecord], # old orignal videos.tsv records
               recs_cur: List[VaRecord], # current latest transactional videos.tsv records
               recs: List[VaRecord], # new records to merge based on recs0
               ):
    # TODO: implement merging logic
    return recs


def _set_updated(ctx: VaContext, vr: VaRecord):
    ctx.updated_paths.add(vr.path)
    vr.updated_on = format_tts(time())
    vr.updated_by = UPDATED_BY


# build dated path for output files with structure base_dir/<YYYY>/<MM>/filename.<ext>
def _build_dated_path(vr: VaRecord, base_dir: str, ext: str) -> str:
    path: str = base_dir

    if vr.start_date and vr.start_date != "n/a" and len(vr.start_date) == 10:
        year, month, day = vr.start_date.split("-")
        path = os.path.join(path, year)
        path = os.path.join(path, month)

    os.makedirs(path, exist_ok=True)
    file_name = f"{os.path.basename(vr.path)}.{ext}"
    return os.path.join(path, file_name)


def do_audit_file(ctx: VaContext, path: str) -> Generator[VaRecord, None, None]:
    """Audit a single video file.

    :param ctx: VaContext object with processing context
    :type ctx: VaContext

    :param path: Path to the video file
    :type path: str

    :return: Generator of VaRecord objects
    :rtype: Generator[VaRecord, None, None]
    """

    logger.debug(f"do_audit_file(path={path})")

    # check max files limit
    if 0 <= ctx.max_counter <= ctx.c_internal:
        logger.debug(f"Max files limit reached: {ctx.max_counter}")
        return

    if ctx.skip_names and path in ctx.skip_names:
        logger.info(f"Skipping file by path : {path}")
        return

    # filter by path mask
    if ctx.path_mask and not fnmatch.fnmatch(path, ctx.path_mask):
        logger.info(f"Skipping file by path mask : {path}")
        return

    vr: VaRecord = VaRecord()

    try:
        if os.path.exists(path):
            vr.present = True
            vr.path = path
            vr.name = os.path.basename(path)

            if ctx.skip_names and vr.name in ctx.skip_names:
                logger.info(f"Skipping file by name : {vr.name}")
                return

            # try to find session_begin in log file
            sb = find_metadata_json(path + ".log", "type", "session_begin")
            if sb is not None:
                logger.debug(f"sb: {sb}")
                vr.video_fps_detected = sb["frameRate"]
                vr.video_res_detected = f"{sb['cx']}x{sb['cy']}"

            vi: InfoSummary
            vti: VideoTimeInfo
            vi, vti = do_info_file(path, True)
            logger.debug(f"vi: {vi}")
            logger.debug(f"vti: {vi}")

            if vti is not None:
                vr.start_date = format_date(vti.start_time)
                vr.start_time = format_time(vti.start_time)
                vr.end_date = format_date(vti.end_time)
                vr.end_time = format_time(vti.end_time)
                if vti.end_time is not None:
                    vr.complete = True

            if vi is not None:
                if vi.duration_sec is not None:
                    vr.video_dur_detected = str(round(vi.duration_sec, 1))
                    vr.duration = vr.video_dur_detected
                    vr.duration_h = format_duration(vi.duration_sec)
                if vi.size_mb is not None:
                    vr.video_size_mb = str(vi.size_mb)
                if vi.rate_mbpm is not None:
                    vr.video_rate_mbpm = str(vi.rate_mbpm)

                ps: ParseSummary = next(do_parse(path, True, True))
                logger.info(f"ps: {ps}")
                if ps is not None:
                    if (
                        ps.video_duration is not None
                        and 0 <= ps.video_duration < 604800.0
                    ):
                        vr.video_dur_recorded = str(round(ps.video_duration, 1))

                    if vr.duration is None or vr.duration == "n/a":
                        video_duration = ps.video_duration
                        if video_duration is not None:
                            if 0 <= video_duration < 604800.0:
                                vr.duration = str(round(video_duration, 1))
                                vr.duration_h = format_duration(video_duration)
                            else:
                                video_duration = None
                    # vr.start_date = format_date(ps.video_isotime_start)
                    # vr.start_time = format_time(ps.video_isotime_start)
                    # vr.end_date = format_date(ps.video_isotime_end)
                    # vr.end_time = format_time(ps.video_isotime_end)
                    # if ps.video_isotime_end is not None:
                    #    vr.complete = True
                    vr.video_res_recorded = (
                        f"{ps.video_frame_width}x{ps.video_frame_height}"
                    )
                    vr.video_fps_recorded = f"{round(ps.video_frame_rate, 1)}"

            # try to get audio info
            ai: AudioInfo = get_audio_info_ffprobe(path)
            if ai is not None:
                logger.debug(f"ai: {ai}")
                if ai.sample_rate is not None:
                    vr.audio_sr = f"{ai.sample_rate}Hz"
                if ai.bits_per_sample is not None:
                    vr.audio_sr += f" {ai.bits_per_sample}b"
                if ai.channels is not None:
                    vr.audio_sr += f" {ai.channels}ch"
                if ai.codec is not None:
                    vr.audio_sr += f" {ai.codec}"
                if ai.duration_sec is not None:
                    vr.audio_dur = str(round(ai.duration_sec, 1))
                    if vr.duration == "n/a" or vr.duration is None:
                        vr.duration = vr.audio_dur
                        vr.duration_h = format_duration(ai.duration_sec)

    # catch all exceptions
    except Exception as e:
        logger.error(f"Unhandled exception occurred when processing file: {path}")
        logger.error(f"Details: {e}")
        logger.error(traceback.format_exc())  # logs full stack trace

    vr.file_log_coherent = check_coherent(vr)
    _set_updated(ctx, vr)
    ctx.c_internal += 1
    logger.debug(f"c_internal -> {ctx.c_internal}")
    yield vr


def do_audit_dir(
    ctx:  VaContext,
    path: str
) -> Generator[VaRecord, None, None]:
    """Audit video files in directory with .mkv, .mp4, .avi extensions.

    :param ctx: VaContext object with processing context
    :type ctx: VaContext

    :param path: Path to the directory
    :type path: str

    :return: Generator of VaRecord objects
    :rtype: Generator[VaRecord, None, None]
    """
    logger.debug(f"do_audit_dir(path={path}, recursive={ctx.recursive})")

    # check max files limit
    if 0 <= ctx.max_counter <= ctx.c_internal:
        logger.debug(f"Max files limit reached: {ctx.max_counter}")
        return

    # check if path exists
    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return

    # check if path is a directory
    if not os.path.isdir(path):
        logger.error(f"Path is not a directory: {path}")
        return

    if ctx.skip_names and path in ctx.skip_names:
        logger.info(f"Skipping directory by path : {path}")
        return

    for name in sorted(os.listdir(path)):
        path2 = os.path.join(path, name)
        if os.path.isfile(path2) and name.lower().endswith((".mkv", ".mp4", ".avi")):
            logger.debug(f"Found video: {path2}")
            yield from do_audit_file(ctx, path2)
        elif ctx.recursive and os.path.isdir(path2):
            logger.debug(f"Descending into directory: {path2}")
            yield from do_audit_dir(ctx, path2)


def do_audit_internal(
    ctx: VaContext,
    paths_dir_or_file: List[str]
) -> Generator[VaRecord, None, None]:
    """Audit a single video file or all video files in a directory.

    :param ctx: VaContext object with processing context
    :type ctx: VaContext

    :param paths_dir_or_file: List of path to the video file or directory
    :type paths_dir_or_file: List[str]

    :return: Generator of VaRecord objects
    :rtype: Generator[VaRecord, None, None]
    """
    logger.debug(
        f"do_audit_internal(paths_dir_or_file={paths_dir_or_file}, " f"recursive={ctx.recursive})"
    )

    # check source is INTERNAL or ALL
    if not ctx.source & {VaSource.INTERNAL, VaSource.ALL}:
        logger.debug("Skipping internal source as per context")
        return

    # prevent run for RERUN_FOR_NA mode
    if ctx.mode == VaMode.RERUN_FOR_NA:
        logger.debug("Skipping internal source for rerun-for-na mode")
        return

    # prevent run for RESET_TO_NA mode
    if ctx.mode == VaMode.RESET_TO_NA:
        logger.debug("Skipping internal source for reset-to-na mode")
        return

    for path in paths_dir_or_file:
        if not os.path.exists(path):
            logger.error(f"Path does not exist: {path}")
            return

        if os.path.isfile(path):
            yield from do_audit_file(ctx, path)
        elif os.path.isdir(path):
            yield from do_audit_dir(ctx, path)


def run_ext_nosignal(ctx: VaContext, vr: VaRecord) -> VaRecord:
    """Run detect-noscreen external tools on the specified VaRecord.

    :param ctx: VaContext object with processing context
    :type ctx: VaContext

    :param vr: VaRecord object to process
    :type vr: VaRecord

    :return: Updated VaRecord object
    :rtype: VaRecord
    """
    logger.debug(f"run_ext_nosignal(path={vr.path}, no_signal_frames={vr.no_signal_frames})")

    # check mode is NOSIGNAL or ALL
    if not ctx.source & {VaSource.NOSIGNAL, VaSource.ALL}:
        logger.debug("Skipping nosignal source as per context")
        return vr

    # check max files limit
    if 0 <= ctx.max_counter <= ctx.c_nosignal:
        logger.debug(f"Max nosignal limit reached: {ctx.max_counter}")
        return vr

    # filter by path mask
    if ctx.path_mask and not fnmatch.fnmatch(vr.path, ctx.path_mask):
        logger.info(f"Skipping nosignal by path mask : {vr.path}")
        return vr

    # reset related fields to n/a if any
    if ctx.mode == VaMode.RESET_TO_NA:
        if vr.no_signal_frames != "n/a":
            vr.no_signal_frames = "n/a"
            logger.debug(f"Reset no_signal_frames -> {vr.no_signal_frames}")
            _set_updated(ctx, vr)
            ctx.c_nosignal += 1
            logger.debug(f"c_nosignal -> {ctx.c_nosignal}")
        return vr

    if ctx.mode == VaMode.RERUN_FOR_NA:
        if vr.no_signal_frames != "n/a":
            logger.debug("Skipping nosignal source as per context (not n/a)")
            return vr

    # make sure data and logs dirs exist
    os.makedirs(ctx.nosignal_data_dir, exist_ok=True)
    os.makedirs(ctx.nosignal_log_dir, exist_ok=True)

    # build paths
    base_name = os.path.basename(vr.path)
    json_path = _build_dated_path(vr, ctx.nosignal_data_dir, "nosignal.json")
    log_path = _build_dated_path(vr, ctx.nosignal_log_dir, "nosignal.log")

    # prepare command-line to run
    cmd = ["reprostim"]

    # optionally add log level
    if ctx.log_level is not None:
        cmd += ["--log-level", ctx.log_level]

    cmd += ["detect-noscreen"]
    cmd += ctx.nosignal_opts
    cmd += ["--output", json_path]
    cmd += [vr.path]
    logger.debug(f"cmd: {' '.join(cmd)}")

    # run the command and capture output
    try:
        with open(log_path, "w", encoding="utf-8") as log_file:
            result = subprocess.run(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                check=True,
            )
            logger.debug(f"detect-noscreen completed with return code {result.returncode}")
    except subprocess.CalledProcessError as e:
        logger.error(f"detect-noscreen failed: {e} {e.stdout} {e.stderr}")
        return vr

    # now read the output JSON file
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                logger.debug(f"detect-noscreen output data: {data}")
                if "nosignal_rate" in data:
                    vr.no_signal_frames = f"{float(data['nosignal_rate']) * 100:.1f}"
                else:
                    vr.no_signal_frames = "0.0"
            logger.debug(f"Set no_signal_frames -> {vr.no_signal_frames}")
            _set_updated(ctx, vr)
            ctx.c_nosignal += 1
            logger.debug(f"c_nosignal -> {ctx.c_nosignal}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read/parse nosignal JSON output: {e}")
    return vr


def run_ext_qr(ctx: VaContext, vr: VaRecord) -> VaRecord:
    """Run qr-parse external tool on the specified VaRecord.

    :param ctx: VaContext object with processing context
    :type ctx: VaContext

    :param vr: VaRecord object to process
    :type vr: VaRecord

    :return: Updated VaRecord object
    :rtype: VaRecord
    """

    logger.debug(f"run_ext_qr(path={vr.path}, qr_records_number={vr.qr_records_number})")

    # check mode is QR or ALL
    if not ctx.source & {VaSource.QR, VaSource.ALL}:
        logger.debug("Skipping qr source as per context")
        return vr

    # check max files limit
    if 0 <= ctx.max_counter <= ctx.c_qr:
        logger.debug(f"Max qr limit reached: {ctx.max_counter}")
        return vr

    # filter by path mask
    if ctx.path_mask and not fnmatch.fnmatch(vr.path, ctx.path_mask):
        logger.info(f"Skipping qr by path mask : {vr.path}")
        return vr

    # reset related fields to n/a if any
    if ctx.mode == VaMode.RESET_TO_NA:
        if vr.qr_records_number != "n/a":
            vr.qr_records_number = "n/a"
            logger.debug(f"Reset qr_records_number -> {vr.qr_records_number}")
            _set_updated(ctx, vr)
            ctx.c_qr += 1
            logger.debug(f"c_qr -> {ctx.c_qr}")
        return vr

    if ctx.mode == VaMode.RERUN_FOR_NA:
        if vr.qr_records_number != "n/a":
            logger.debug("Skipping qr source as per context (not n/a)")
            return vr

    # make sure data and logs dirs exist
    os.makedirs(ctx.qr_data_dir, exist_ok=True)
    os.makedirs(ctx.qr_log_dir, exist_ok=True)

    # build paths
    base_name = os.path.basename(vr.path)
    jsonl_path = _build_dated_path(vr, ctx.qr_data_dir, "qrinfo.jsonl")
    log_path = _build_dated_path(vr, ctx.qr_log_dir, "qrinfo.log")
    ffmpeg_log_path = _build_dated_path(vr, ctx.qr_log_dir, "ffmpeg.log")


    with (tempfile.TemporaryDirectory() as tmpdir):
        logger.debug(f"tmpdir : {tmpdir}")

        tmp_video: str = os.path.join(tmpdir, base_name)
        logger.debug(f"tmp_video : {tmp_video}")

        try:
            # convert to mkv without audio
            # like: ffmpeg -i "$file" -an -c copy "$tmp_mkv_file"
            logger.debug(f"ffmpeg_log_path : {ffmpeg_log_path}")
            with open(ffmpeg_log_path, "w", encoding="utf-8") as ffmpeg_log_file:
                cmd = [
                    "ffmpeg",
                    "-i", vr.path,
                    "-an",
                    "-c", "copy",
                    tmp_video
                ]
                logger.debug(f"cmd: {' '.join(cmd)}")
                result = subprocess.run(cmd,
                               stdout = ffmpeg_log_file,
                               stderr = subprocess.STDOUT,
                               text = True,
                               check = True,)
                logger.debug(f"ffmpeg completed with return code {result.returncode}")

            # execute qr-parse action like below:
            #
            # reprostim --log-level $LOG_LEVEL
            #   qr-parse "$tmp_mkv_file"
            #   >"$OUT_DIR"/"$base_name".qrinfo.jsonl
            #   2>"$OUT_DIR"/"$base_name".qrinfo.log
            #

            # prepare command-line to run
            cmd = ["reprostim"]

            # optionally add log level
            if ctx.log_level is not None:
                cmd += ["--log-level", ctx.log_level]

            cmd += ["qr-parse"]
            cmd += ctx.qr_opts
            cmd += [tmp_video]
            logger.debug(f"cmd: {' '.join(cmd)}")

            # run reprostim qr-parse command and capture output
            logger.debug(f"log_path: {log_path}")
            logger.debug(f"jsonl_path: {jsonl_path}")
            with open(log_path, "w", encoding="utf-8") as log_file:
                with open(jsonl_path, "w", encoding="utf-8") as jsonl_file:
                    result = subprocess.run(
                        cmd,
                        stdout=jsonl_file,
                        stderr=log_file,
                        text=True,
                        check=True,
                    )
                    logger.debug(f"qr-parse completed with return code {result.returncode}")

            # now read the output JSON file
            if os.path.exists(jsonl_path):
                try:
                    with open(jsonl_path, "r", encoding="utf-8") as f:
                        for line in f:
                            record = json.loads(line)
                            if record.get('type') == 'ParseSummary':
                                logger.debug(f"qr-parse summary: {record}")
                                vr.qr_records_number = str(record.get('qr_count', '0'))
                                logger.debug(f"Set qr_records_number -> {vr.qr_records_number}")
                                _set_updated(ctx, vr)
                                ctx.c_qr += 1
                                logger.debug(f"c_qr -> {ctx.c_qr}")
                                break
                except (json.JSONDecodeError, IOError) as e:
                    logger.error(f"Failed to read/parse qr JSON output: {e}")

        except subprocess.CalledProcessError as e:
            logger.error(f"qr failed: {e} {e.stdout} {e.stderr}")

    return vr


def run_ext_all(ctx: VaContext, vr: VaRecord) -> VaRecord:
    """Run all external tools on the specified VaRecord.

    :param ctx: VaContext object with processing context
    :type ctx: VaContext

    :param vr: VaRecord object to process
    :type vr: VaRecord

    :return: Updated VaRecord object
    :rtype: VaRecord
    """
    logger.debug(f"run_ext_all(path={vr.path})")
    return run_ext_qr(ctx, run_ext_nosignal(ctx, vr))


def do_audit(ctx: VaContext, paths_dir_or_file: List[str]) -> Generator[VaRecord, None, None]:
    """Generator that audits files and applies all external tools to
    each record if any, depending on context and options.
    """
    logger.debug(f"do_audit(paths_dir_or_file={paths_dir_or_file})")
    for rec in do_audit_internal(ctx, paths_dir_or_file):
        yield run_ext_all(ctx, rec)


def do_ext(ctx: VaContext, recs: List[VaRecord]) -> Generator[VaRecord, None, None]:
    """Generator that runs external tools on existing records
    depending on context and options.
    """
    logger.debug(f"do_ext(...)")
    for rec in recs:
        yield run_ext_all(ctx, rec)


def do_main(
    paths: List[str],
    path_tsv: str,
    recursive: bool = False,
    mode: VaMode = VaMode.INCREMENTAL,
    va_src: Set[VaSource] = {VaSource.INTERNAL},
    max_files: int = -1,
    path_mask: str = None,
    verbose: bool = False,
    out_func=print,
):
    """The main function invoked by CLI to analyze video files with
    logs and save the results to a TSV file.

    :param paths: One or more paths to the video file or directory
    :type paths: List[str]

    :param path_tsv: Path to the output TSV file, default 'videos.tsv'.
    :type path_tsv: str

    :param recursive: Whether to scan directories recursively. Default: False
    :type recursive: bool

    :param mode: Operation mode, one of VaMode values (default: INCREMENTAL)
    :type mode: VaMode

    :param va_src: Set of VaSource values to specify audit sources
    :type va_src: Set[VaSource]

    :param max_files: Maximum number of video files/records to process.
                      Use -1 for unlimited (default: -1)
    :type max_files: int

    :param path_mask: Optional fnmatch-style mask to filter files
    :type path_mask: str

    :param verbose: Whether to print verbose JSON output
                    to stdout (default: False)
    :type verbose: bool

    :param out_func: Function to stdout results (default: print)
    :type out_func: Callable[[str], None]

    :return: 0 on success, 1 on failure
    :rtype: int
    """

    logger.debug("video-audit command")
    logger.debug(f"paths     : {paths}")
    logger.debug(f"path_tsv  : {path_tsv}")

    # double validate each path is valid and exists
    for path in paths:
        if not os.path.exists(path):
            logger.error(f"Path does not exist: {path}")
            return 1

    if not check_ffprobe():
        out_func(
            "Error: ffprobe is not installed. Make sure" " ffmpeg package is installed."
        )
        logger.error(
            "!!! ffprobe is required to parse audio but"
            " not found. Make sure ffmpeg package is installed."
        )

    lock = FileLock(f"{path_tsv}.lock")

    recs0: List[VaRecord] = []
    # in case path_tsv exists, and mode is not FULL,
    # load existing records
    if mode != VaMode.FULL and os.path.exists(path_tsv):
        logger.info(f"Loading existing TSV file: {path_tsv}")
        with lock:
            recs0 = _load_tsv(path_tsv)
        logger.info(f"Loaded {len(recs0)} existing records from TSV")

    # skip files set in case of INCREMENTAL mode
    skip_names = None
    if mode == VaMode.INCREMENTAL and len(recs0) > 0:
        skip_names = {r.name for r in recs0}

    # collect all records from generator into a list
    # setup audit context first
    ctx: VaContext = VaContext(
        skip_names=skip_names,
        c_internal=0,
        c_nosignal=0,
        c_qr=0,
        log_level=os.environ["REPROSTIM_LOG_LEVEL"],
        max_counter=max_files,
        mode=mode,
        path_mask=path_mask,
        recursive=recursive,
        source=va_src,
    )
    recs1: List[VaRecord] = list(do_audit(ctx, paths))

    if verbose:
        for vr in recs1:
            out_func(f"{vr.model_dump_json()}")

    # merge recs0 and recs1, with recs1 taking precedence by .name key
    recs = recs1
    if len(recs0) > 0:
        merged_dict = {r.name: r for r in recs0}
        merged_dict.update({r.name: r for r in recs1})
        recs = list(merged_dict.values())

    if mode in {VaMode.RERUN_FOR_NA, VaMode.RESET_TO_NA}:
        recs = list(do_ext(ctx, recs))

    logger.info(f"Audited records count: {len(ctx.updated_paths)}")
    logger.info(f"Saving results to TSV file : {path_tsv}")
    logger.info(f"Total records to save      : {len(recs)}")
    # sort records by name
    recs.sort(key=lambda r: r.name)
    with lock:
        recs_cur: List[VaRecord] = _load_tsv(path_tsv)
        recs = _merge_recs(ctx, recs0, recs_cur, recs)
        _save_tsv(recs, path_tsv)

    return 0
