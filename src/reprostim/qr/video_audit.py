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
import logging
import os
import re
import socket
import subprocess
import traceback
from datetime import datetime
from enum import Enum
from time import time
from typing import Dict, Generator, List, Set, Optional

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
    Intended for run external slow tools like detect-nosignal 
    or qr-parser."""


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


def do_audit_file(
    path: str, skip_names: Optional[set] = None
) -> Generator[VaRecord, None, None]:
    """Audit a single video file.

    :param path: Path to the video file
    :type path: str

    :param skip_names: Optional set of file base names
                       to skip (for incremental mode)
    :type skip_names: Optional[set]

    :return: Generator of VaRecord objects
    :rtype: Generator[VaRecord, None, None]
    """

    logger.debug(f"do_audit_file(path={path})")

    if skip_names and path in skip_names:
        logger.info(f"Skipping file by path : {path}")
        return

    vr: VaRecord = VaRecord()

    try:
        if os.path.exists(path):
            vr.present = True
            vr.path = path
            vr.name = os.path.basename(path)

            if skip_names and vr.name in skip_names:
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
    vr.updated_on = format_tts(time())
    vr.updated_by = UPDATED_BY
    yield vr


def do_audit_dir(
    path: str, recursive: bool = False, skip_names: Optional[set] = None
) -> Generator[VaRecord, None, None]:
    """Audit video files in directory with .mkv, .mp4, .avi extensions.

    :param path: Path to the directory
    :type path: str

    :param recursive: Whether to scan directories recursively. Default: False
    :type recursive: bool

    :param skip_names: Optional set of file base names
                       to skip (for incremental mode)
    :type  skip_names: Optional[set]

    :return: Generator of VaRecord objects
    :rtype: Generator[VaRecord, None, None]
    """
    logger.debug(f"do_audit_dir(path={path}, recursive={recursive})")

    # check if path exists
    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return

    # check if path is a directory
    if not os.path.isdir(path):
        logger.error(f"Path is not a directory: {path}")
        return

    if skip_names and path in skip_names:
        logger.info(f"Skipping directory by path : {path}")
        return

    for name in sorted(os.listdir(path)):
        path2 = os.path.join(path, name)
        if os.path.isfile(path2) and name.lower().endswith((".mkv", ".mp4", ".avi")):
            logger.debug(f"Found video: {path2}")
            yield from do_audit_file(path2, skip_names)
        elif recursive and os.path.isdir(path2):
            logger.debug(f"Descending into directory: {path2}")
            yield from do_audit_dir(path2, recursive, skip_names)


def do_audit(
    path_dir_or_file: str, recursive: bool = False, skip_names: Optional[set] = None
) -> Generator[VaRecord, None, None]:
    """Audit a single video file or all video files in a directory.

    :param path_dir_or_file: Path to the video file or directory
    :type path_dir_or_file: str

    :param recursive: Whether to scan directories recursively. Default: False
    :type recursive: bool

    :return: Generator of VaRecord objects
    :rtype: Generator[VaRecord, None, None]
    """
    logger.debug(
        f"do_audit(path_dir_or_file={path_dir_or_file}, " f"recursive={recursive})"
    )
    if not os.path.exists(path_dir_or_file):
        logger.error(f"Path does not exist: {path_dir_or_file}")
        return

    if os.path.isfile(path_dir_or_file):
        yield from do_audit_file(path_dir_or_file, skip_names)
    elif os.path.isdir(path_dir_or_file):
        yield from do_audit_dir(path_dir_or_file, recursive, skip_names)


def do_main(
    path: str,
    path_tsv: str,
    recursive: bool = False,
    mode: VaMode = VaMode.INCREMENTAL,
    va_src: Set[VaSource] = {VaSource.INTERNAL},
    max_files: int = -1,
    verbose: bool = False,
    out_func=print,
):
    """The main function invoked by CLI to analyze video files with
    logs and save the results to a TSV file.

    :param path: Path to the video file or directory
    :type path: str

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

    :param verbose: Whether to print verbose JSON output
                    to stdout (default: False)
    :type verbose: bool

    :param out_func: Function to stdout results (default: print)
    :type out_func: Callable[[str], None]

    :return: 0 on success, 1 on failure
    :rtype: int
    """

    logger.debug("video-audit command")
    logger.debug(f"path      : {path}")
    logger.debug(f"path_tsv  : {path_tsv}")

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

    recs0: List[VaRecord] = []
    # in case path_tsv exists, and mode is not FULL,
    # load existing records
    if mode != VaMode.FULL and os.path.exists(path_tsv):
        logger.info(f"Loading existing TSV file: {path_tsv}")
        recs0 = _load_tsv(path_tsv)
        logger.info(f"Loaded {len(recs0)} existing records from TSV")

    # skip files set in case of INCREMENTAL mode
    skip_names = None
    if mode == VaMode.INCREMENTAL and len(recs0) > 0:
        skip_names = {r.name for r in recs0}

    # collect all records from generator into a list
    recs1: List[VaRecord] = list(do_audit(path, recursive, skip_names))
    logger.info(f"Audited records count: {len(recs1)}")

    if verbose:
        for vr in recs1:
            out_func(f"{vr.model_dump_json()}")

    # merge recs0 and recs1, with recs1 taking precedence by .name key
    recs = recs1
    if len(recs0) > 0:
        merged_dict = {r.name: r for r in recs0}
        merged_dict.update({r.name: r for r in recs1})
        recs = list(merged_dict.values())

    logger.info(f"Saving results to TSV file : {path_tsv}")
    logger.info(f"Total records to save      : {len(recs)}")
    # sort records by name
    recs.sort(key=lambda r: r.name)
    _save_tsv(recs, path_tsv)

    return 0
