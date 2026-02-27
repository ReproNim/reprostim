# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
API to split and audit video files recorded by reprostim-videocapture,
along with their corresponding log files and QR/audio metadata.
"""

import logging
import os
import subprocess
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Optional

import isodate
from pydantic import BaseModel, Field

from reprostim.qr.video_audit import VaRecord, find_metadata_json, get_file_video_audit

# initialize the logger
# Note: all logs out to stderr
logger = logging.getLogger(__name__)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.debug(f"name={__name__}")


class BufferPolicy(str, Enum):
    """Policy for handling buffer overflow beyond video boundaries."""

    STRICT = "strict"
    FLEXIBLE = "flexible"


class VideoSegment(BaseModel):
    """Specifies a video segment data."""

    start_ts: Optional[datetime] = None  # Start timestamp
    end_ts: Optional[datetime] = None  # End timestamp
    offset_sec: Optional[float] = None  # Offset in seconds within video file
    offset_frame: Optional[int] = None  # Offset frame number within video file
    duration_sec: Optional[float] = None  # Duration in seconds
    frame_count: Optional[int] = None  # Number of frames


class SplitData(BaseModel):
    """Specifies metadata necessary to split single video file."""

    success: bool = False  # Whether split data calculation was successful
    path: str = "n/a"  # Path to the .mkv video file
    fps: Optional[float] = None  # Frames per second
    resolution: Optional[str] = None  # Video resolution (e.g., '1920x1080')
    audio_sr: Optional[str] = None  # Audio sample rate (e.g., '48000 Hz')
    device: str = "n/a"  # Video-audio capture device name
    device_serial_number: str = "n/a"  # Video-audio capture device serial number
    full_seg: Optional[VideoSegment] = None  # specifies entire video segment
    sel_seg: Optional[VideoSegment] = None  # specifies exact split video selection
    buf_seg: Optional[VideoSegment] = None  # specifies selection with buffer around


class SplitResult(BaseModel):
    """Specifies result of video split operation."""

    success: bool = Field(False, exclude=True)  # Whether split operation was successful
    input_path: str = Field("n/a", exclude=True)  # Path to the input .mkv video file
    output_path: str = Field("n/a", exclude=True)  # Path to the output .mkv video file
    buffer_before: Optional[float] = None  # Buffer before in seconds
    buffer_after: Optional[float] = None  # Buffer after in seconds
    buffer_duration: Optional[float] = None  # Total buffer duration in seconds
    start_time: Optional[datetime] = Field(
        None, exclude=True
    )  # Start time of the split segment
    end_time: Optional[datetime] = Field(
        None, exclude=True
    )  # End time of the split segment
    duration: Optional[float] = None  # Duration of the split segment in seconds
    video_width: str = "n/a"  # Video width in pixels (e.g., '1920')
    video_height: str = "n/a"  # Video height in pixels (e.g., '1080')
    video_frame_rate: Optional[float] = None  # Video frames per second
    video_size_mb: Optional[float] = None  # Video file size in megabytes
    video_rate_mbpm: Optional[float] = None  # Video bitrate in megabits per second
    audio_sample_rate: str = "n/a"  # Audio sample rate in Hz (e.g., '48000')
    audio_bit_depth: str = "n/a"  # Audio bit depth (hardcoded to '16')
    audio_channel_count: str = "n/a"  # Number of audio channels (e.g., '2')
    audio_codec: str = "n/a"  # Audio codec name (e.g., 'aac')
    # orig_ prefixed fields at the end - describe original video timing
    #  context (BIDS compliance)
    orig_buffer_start: str = "n/a"  # Start time of the buffer in ISO 8601 format
    orig_buffer_end: str = "n/a"  # End time of the buffer in ISO 8601 format
    orig_buffer_offset: Optional[float] = None  # Buffer start offset in seconds
    orig_start: str = "n/a"  # Start time of the split segment only in ISO 8601 format
    orig_end: str = "n/a"  # End time of the split segment only in ISO 8601 format
    orig_offset: Optional[float] = None  # Offset of the split segment in seconds
    orig_device: str = "n/a"  # Video-audio capture device name
    orig_device_serial_number: str = "n/a"  # Video-audio capture device serial number


def _parse_audio_info(audio_info: Optional[str]) -> dict:
    """Parse audio_info string into separate BIDS-style fields.

    Parses format like '48000Hz 16b 2ch aac' into individual fields.
    Returns n/a for all fields if parsing fails.

    :param audio_info: Audio info string (e.g., '48000Hz 2ch aac')
    :type audio_info: Optional[str]
    :return: Dict with audio_sample_rate, audio_bit_depth,
             audio_channel_count, audio_codec
    :rtype: dict
    """
    na = {
        "audio_sample_rate": "n/a",
        "audio_bit_depth": "n/a",
        "audio_channel_count": "n/a",
        "audio_codec": "n/a",
    }
    if not audio_info or audio_info == "n/a":
        return na

    try:
        result = dict(na)
        for part in audio_info.split():
            if part.endswith("Hz"):
                result["audio_sample_rate"] = part[:-2]
            elif part.endswith("b") and part[:-1].isdigit():
                result["audio_bit_depth"] = part[:-1]
            elif part.endswith("ch") and part[:-2].isdigit():
                result["audio_channel_count"] = part[:-2]
            else:
                result["audio_codec"] = part
        # hardcode bit depth to 16 if not parsed
        if result["audio_bit_depth"] == "n/a":
            result["audio_bit_depth"] = "16"
        return result
    except Exception:
        return na


def _format_time(dt: datetime) -> str:
    """Format datetime object to ISO 8601 time string.

    :param dt: Datetime object
    :type dt: datetime
    :return: Formatted time string in ISO 8601 format (e.g., '17:30:00.321')
    :rtype: str
    """
    return dt.isoformat(timespec="milliseconds").split("T")[1]


def _parse_date_time(date_str: str, time_str: str) -> datetime:
    """Parse date and time strings to datetime object.

    :param date_str: Date string in ISO 8601 format (e.g., '2024-02-02')
    :type date_str: str
    :param time_str: Time string in ISO 8601 format (e.g., '17:30:00.321')
    :type time_str: str
    :return: Parsed datetime object
    :rtype: datetime
    :raises ValueError: If the date or time string is not in valid format
    """
    try:
        dt = datetime.fromisoformat(f"{date_str}T{time_str}")
        return dt
    except ValueError as e:
        logger.error(f"Invalid date/time format: {date_str} {time_str}")
        raise e


def _parse_fps(fps_str: str) -> float:
    """Parse fps string to float.

    :param fps_str: FPS string
    :type fps_str: str

    :return: FPS as float
    :rtype: float
    :raises ValueError: If the fps string is not in valid format
    """
    try:
        if fps_str == "n/a" or not fps_str:
            return 0.0
        return float(fps_str)
    except ValueError as e:
        logger.error(f"Invalid fps format: {fps_str}")
        raise e


def _parse_interval_sec(interval_str: str) -> float:
    """Parse interval string to float seconds.

    :param interval_str: Interval string (either float seconds or ISO 8601 duration)
    :type interval_str: str
    :return: Interval in float seconds
    :rtype: float
    :raises ValueError: If the interval string is not in valid format
    """
    try:
        if not interval_str or interval_str == "n/a":
            return 0.0
        # first try parsing as ISO 8601 duration
        duration = isodate.parse_duration(interval_str)
        return duration.total_seconds()
    except ValueError:
        try:
            return float(interval_str)
        except ValueError:
            logger.error(f"Invalid interval format: {interval_str}")
            raise


def _parse_ts(time_str: str | None, time_only: bool = False) -> datetime:
    """Parse time string to datetime object.

    Accepts:
    - Full ISO 8601 datetime: '2024-02-02T17:30:00'
    - Time-only (with or without T prefix): '17:30:00', 'T17:30:00'
    - Numeric seconds offset from midnight: '300', '300.5'

    :param time_str: Time string in ISO 8601 format, or numeric seconds
    :type time_str: str

    :param time_only: If True, parse time only without date (default: False)
    :type time_only: bool

    :return: Parsed datetime object
    :rtype: datetime
    :raises ValueError: If the time string is not in valid format
    """
    try:
        if not time_str:
            return None

        # Try numeric seconds first (e.g., '300', '300.5')
        try:
            sec = float(time_str)
            return datetime.combine(date.today(), time.min) + timedelta(seconds=sec)
        except ValueError:
            pass

        # Strip leading 'T' for time-only strings like 'T17:30:00'
        ts = time_str
        if time_str.startswith("T") and len(time_str) > 1:
            ts = time_str[1:]

        try:
            dt = datetime.fromisoformat(ts)
            if time_only:
                dt = datetime.combine(date.today(), dt.time())
            return dt
        except ValueError as e2:
            if time_only:
                t = time.fromisoformat(ts)
                return datetime.combine(date.today(), t)
            else:
                raise e2

    except ValueError as e:
        logger.error(f"Invalid time format: {time_str}")
        raise e


class SpecEntry(BaseModel):
    """Parsed representation of a single --spec argument."""

    start_str: str
    duration_str: Optional[str] = None
    end_str: Optional[str] = None


# Template tokens supported in --output and --sidecar-json paths
_TEMPLATE_TOKENS = ["{n}", "{start}", "{end}", "{duration}"]


def _parse_spec(spec_str: str) -> SpecEntry:
    """Parse a --spec argument string into a SpecEntry.

    Format:
    - START/DURATION  (single slash = duration)
    - START//END      (double slash = end time)

    :param spec_str: Spec string to parse
    :type spec_str: str
    :return: Parsed SpecEntry
    :rtype: SpecEntry
    :raises ValueError: If the spec string format is invalid
    """
    if "//" in spec_str:
        parts = spec_str.split("//", 1)
        if not parts[0].strip() or not parts[1].strip():
            raise ValueError(
                f"Invalid --spec format: '{spec_str}'. "
                f"Expected START//END (e.g., '17:30:00//17:33:00')"
            )
        return SpecEntry(start_str=parts[0].strip(), end_str=parts[1].strip())
    elif "/" in spec_str:
        parts = spec_str.split("/", 1)
        if not parts[0].strip() or not parts[1].strip():
            raise ValueError(
                f"Invalid --spec format: '{spec_str}'. "
                f"Expected START/DURATION (e.g., '17:30:00/PT3M')"
            )
        return SpecEntry(start_str=parts[0].strip(), duration_str=parts[1].strip())
    else:
        raise ValueError(
            f"Invalid --spec format: '{spec_str}'. "
            f"Must contain '/' for duration or '//' for end time. "
            f"Examples: '17:30:00/PT3M' or '17:30:00//17:33:00'"
        )


def _format_time_dots(dt: datetime) -> str:
    """Format datetime to dot-separated time string: HH.MM.SS.mmm

    :param dt: Datetime object
    :type dt: datetime
    :return: Formatted time string (e.g., '17.30.00.000')
    :rtype: str
    """
    return dt.strftime("%H.%M.%S.") + f"{dt.microsecond // 1000:03d}"


def _expand_output_template(
    template: str, index: int, start_dt: datetime, end_dt: datetime, duration_sec: float
) -> str:
    """Expand template tokens in output path.

    Tokens:
    - {n}        : 1-based zero-padded index (width 3)
    - {start}    : Formatted start time with dots (e.g., '17.30.00.000')
    - {end}      : Formatted end time with dots
    - {duration} : Duration in seconds (e.g., '180.0')

    :param template: Output path template
    :param index: 1-based segment index
    :param start_dt: Start datetime
    :param end_dt: End datetime
    :param duration_sec: Duration in seconds
    :return: Expanded output path
    """
    return (
        template.replace("{n}", f"{index:03d}")
        .replace("{start}", _format_time_dots(start_dt))
        .replace("{end}", _format_time_dots(end_dt))
        .replace("{duration}", f"{duration_sec:.1f}")
    )


def _has_template_tokens(template: str) -> bool:
    """Check whether a string contains any output template tokens.

    :param template: String to check
    :return: True if any template token is found
    """
    return any(tok in template for tok in _TEMPLATE_TOKENS)


def _calc_split_data(
    path: str,
    sel_start_ts: datetime,
    sel_duration_sec: float,
    sel_end_ts: datetime,
    buf_before_sec: float,
    buf_after_sec: float,
    buffer_policy: BufferPolicy = BufferPolicy.STRICT,
    video_audit_file: str | None = None,
    raw_mode: bool = False,
) -> SplitData:
    """Calculate split data for given video file.

    :param path: Path to the .mkv video file
    :type path: str

    :param sel_start_ts: Selected start timestamp
    :type sel_start_ts: datetime

    :param sel_duration_sec: Selected duration in seconds
    :type sel_duration_sec: float

    :param sel_end_ts: Selected end timestamp
    :type sel_end_ts: datetime

    :param buf_before_sec: Buffer before selection in seconds
    :type buf_before_sec: float

    :param buf_after_sec: Buffer after selection in seconds
    :type buf_after_sec: float

    :param buffer_policy: Policy for handling buffer overflow (strict or flexible)
    :type buffer_policy: BufferPolicy

    :param video_audit_file: Path to video audit TSV file (optional)
    :type video_audit_file: str | None

    :return: SplitData object with metadata
    :rtype: SplitData
    :raises ValueError: If buffer cannot be fulfilled in strict mode
    """
    logger.debug(
        f"_calc_split_data: path={path}, "
        f"sel_start_ts={sel_start_ts}, sel_duration_sec={sel_duration_sec}, "
        f"sel_end_ts={sel_end_ts}, buf_before_sec={buf_before_sec}, "
        f"buf_after_sec={buf_after_sec}, buffer_policy={buffer_policy.value}"
    )

    sd: SplitData = SplitData(success=False, path=path)

    # A) Read video file metadata to get full segment info, fps, frame count etc
    #    as initial implementation use video-audit internal mode
    #    to extract necessary metadata.
    vr: VaRecord = get_file_video_audit(path, video_audit_file, True)
    logger.debug(f"Video audit record: {vr.model_dump_json(indent=2)}")

    # Extract device info from log file session_begin metadata
    # NOTE: in future we may include these columns in videos.tsv audit file
    #       and in this case it can be used directly from VaRecord.
    sb = find_metadata_json(path + ".log", "type", "session_begin")
    if sb is not None:
        sd.device = sb.get("vDev", "n/a") or "n/a"
        sd.device_serial_number = sb.get("serial", "n/a") or "n/a"

    duration_sec: float = _parse_interval_sec(vr.duration)
    if duration_sec <= 0:
        logger.error(
            f"Video duration is zero or negative: {vr.duration}. Most likely "
            f"the video file is corrupted or truncated and need to be fixed first."
        )
        if raw_mode:
            logger.warning(
                "In raw mode, proceeding despite zero/negative duration, it can "
                "produce unpredictable secondary errors."
            )
        else:
            raise ValueError(
                f"Video duration is zero or negative: {duration_sec} seconds."
            )

    # apply fix for raw mode
    if raw_mode:
        # in raw mode, we assume the video starts at time 0
        start_ts: datetime = datetime.combine(sel_start_ts.date(), time.min)
        vr.start_date = start_ts.date().isoformat()
        vr.start_time = start_ts.time().isoformat()
        end_ts: datetime = start_ts + timedelta(seconds=duration_sec)
        vr.end_date = end_ts.date().isoformat()
        vr.end_time = end_ts.time().isoformat()

    sd.fps = _parse_fps(vr.video_fps_recorded)
    sd.resolution = vr.video_res_recorded
    sd.audio_sr = vr.audio_sr
    sd.full_seg = VideoSegment(
        start_ts=_parse_date_time(vr.start_date, vr.start_time),
        end_ts=_parse_date_time(vr.end_date, vr.end_time),
        offset_sec=0.0,
        offset_frame=0,
        duration_sec=duration_sec,
    )
    sd.full_seg.frame_count = int(sd.full_seg.duration_sec * sd.fps)

    # B) Calculate selected segment info
    sel_duration_sec2: float = sel_duration_sec
    sel_end_ts2: datetime = sel_end_ts
    if sel_duration_sec2 is None:
        sel_duration_sec2 = (sel_end_ts - sel_start_ts).total_seconds()
    else:
        sel_end_ts2 = sel_start_ts + timedelta(seconds=sel_duration_sec2)

    sd.sel_seg = VideoSegment(
        start_ts=sel_start_ts,
        end_ts=sel_end_ts2,
        duration_sec=sel_duration_sec2,
    )
    sd.sel_seg.frame_count = int(sd.sel_seg.duration_sec * sd.fps)
    sd.sel_seg.offset_sec = (sd.sel_seg.start_ts - sd.full_seg.start_ts).total_seconds()
    sd.sel_seg.offset_frame = int(sd.sel_seg.offset_sec * sd.fps)

    # C) Calculate buffered segment info
    sd.buf_seg = VideoSegment(
        start_ts=sd.sel_seg.start_ts - timedelta(seconds=buf_before_sec),
        end_ts=sd.sel_seg.end_ts + timedelta(seconds=buf_after_sec),
        duration_sec=sd.sel_seg.duration_sec + buf_before_sec + buf_after_sec,
    )
    sd.buf_seg.frame_count = int(sd.buf_seg.duration_sec * sd.fps)
    sd.buf_seg.offset_sec = (sd.buf_seg.start_ts - sd.full_seg.start_ts).total_seconds()
    sd.buf_seg.offset_frame = int(sd.buf_seg.offset_sec * sd.fps)

    # D) Validate segments against video boundaries and adjust if necessary
    if sd.sel_seg.start_ts < sd.full_seg.start_ts:
        logger.error("Selected start time is before video start.")
        raise ValueError(
            f"Selected start time is before video start: "
            f"{sd.sel_seg.start_ts} < {sd.full_seg.start_ts}."
        )

    if sd.sel_seg.end_ts > sd.full_seg.end_ts:
        logger.error("Selected end time is after video end.")
        raise ValueError(
            f"Selected end time is after video end: "
            f"{sd.sel_seg.end_ts} > {sd.full_seg.end_ts}."
        )

    # Handle buffer overflow based on policy
    buffer_overflow_before = sd.buf_seg.start_ts < sd.full_seg.start_ts
    buffer_overflow_after = sd.buf_seg.end_ts > sd.full_seg.end_ts

    if buffer_policy == BufferPolicy.STRICT:
        if buffer_overflow_before:
            logger.error("Buffer before extends before video start (strict mode).")
            raise ValueError(
                f"Buffer before extends before video start: "
                f"buffer_start={sd.buf_seg.start_ts}, "
                f"video_start={sd.full_seg.start_ts}. "
                f"Use --buffer-policy=flexible to trim buffers automatically."
            )
        if buffer_overflow_after:
            logger.error("Buffer after extends after video end (strict mode).")
            raise ValueError(
                f"Buffer after extends after video end: "
                f"buffer_end={sd.buf_seg.end_ts}, video_end={sd.full_seg.end_ts}. "
                f"Use --buffer-policy=flexible to trim buffers automatically."
            )
    else:  # BufferPolicy.FLEXIBLE
        if buffer_overflow_before:
            logger.warning("Buffer before extends before video start. Trimming buffer.")
            sd.buf_seg.start_ts = sd.full_seg.start_ts
            sd.buf_seg.offset_sec = 0.0
            sd.buf_seg.offset_frame = 0
            sd.buf_seg.duration_sec = (
                sd.buf_seg.end_ts - sd.buf_seg.start_ts
            ).total_seconds()
            sd.buf_seg.frame_count = int(sd.buf_seg.duration_sec * sd.fps)

        if buffer_overflow_after:
            logger.warning("Buffer after extends after video end. Trimming buffer.")
            sd.buf_seg.end_ts = sd.full_seg.end_ts
            sd.buf_seg.duration_sec = (
                sd.buf_seg.end_ts - sd.buf_seg.start_ts
            ).total_seconds()
            sd.buf_seg.frame_count = int(sd.buf_seg.duration_sec * sd.fps)

    sd.success = True
    return sd


def _split_video(sd: SplitData, out_path: str) -> SplitResult:
    """Split video file based on calculated SplitData.

    :param sd: SplitData object with metadata
    :type sd: SplitData

    :return: SplitResult object with result metadata
    :rtype: SplitResult

    :raises NotImplementedError: Function not yet implemented
    """

    # create SplitResult for output
    sr: SplitResult = SplitResult(
        input_path=sd.path,
        output_path=out_path,
        buffer_before=round(
            sd.sel_seg.start_ts.timestamp() - sd.buf_seg.start_ts.timestamp(), 3
        ),
        buffer_after=round(
            sd.buf_seg.end_ts.timestamp() - sd.sel_seg.end_ts.timestamp(), 3
        ),
        orig_buffer_start=_format_time(sd.buf_seg.start_ts),
        orig_buffer_end=_format_time(sd.buf_seg.end_ts),
        buffer_duration=round(sd.buf_seg.duration_sec, 3),
        orig_buffer_offset=round(sd.buf_seg.offset_sec, 3),
        start_time=sd.sel_seg.start_ts,
        duration=sd.sel_seg.duration_sec,
        orig_offset=sd.sel_seg.offset_sec,
        end_time=sd.sel_seg.end_ts,
        video_width=(
            sd.resolution.split("x")[0]
            if sd.resolution and sd.resolution != "n/a"
            else "n/a"
        ),
        video_height=(
            sd.resolution.split("x")[1]
            if sd.resolution and sd.resolution != "n/a"
            else "n/a"
        ),
        video_frame_rate=sd.fps,
        **_parse_audio_info(sd.audio_sr),
        orig_device=sd.device,
        orig_device_serial_number=sd.device_serial_number,
    )

    try:
        cmd = [
            "ffmpeg",
            "-y",  # force overwrite
            "-ss",
            str(sd.buf_seg.offset_sec),
            "-i",
            sd.path,
            "-t",
            str(sd.buf_seg.duration_sec),
            "-c",
            "copy",
            out_path,
        ]
        logger.debug(f"run: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.debug(f"ffmpeg exit code : {str(result.returncode)}")
        logger.debug(f"ffmpeg output    : {str(result.stdout)}")
        logger.debug(f"ffmpeg errors    : {str(result.stderr)}")

        # calculate output video size and rate
        file_size_bytes = os.path.getsize(out_path)
        sr.video_size_mb = round(file_size_bytes / (1024 * 1024), 1)
        if sd.buf_seg.duration_sec > 0:
            sr.video_rate_mbpm = round(
                (file_size_bytes * 8) / (sd.buf_seg.duration_sec * 1024 * 1024), 1
            )
        sr.success = True
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg error: {e} {e.stdout} {e.stderr}")

    if sr.start_time:
        sr.orig_start = _format_time(sr.start_time)

    if sr.end_time:
        sr.orig_end = _format_time(sr.end_time)

    return sr


def _write_sidecar(
    sidecar_path: str, sr: SplitResult, verbose: bool = False, out_func=print
) -> None:
    """Write sidecar JSON file with split result metadata.

    :param sidecar_path: Path to write sidecar JSON file
    :param sr: SplitResult to serialize
    :param verbose: Enable verbose output
    :param out_func: Output function for printing messages
    :raises IOError: If the file cannot be written
    """
    logger.info(f"Writing sidecar JSON to: {sidecar_path}")
    with open(sidecar_path, "w") as f:
        f.write(sr.model_dump_json(indent=2))
        f.write("\n")
    logger.debug("Sidecar JSON file written successfully")
    if verbose:
        out_func(f"Sidecar JSON written to: {sidecar_path}")


def _resolve_sidecar_path(
    sidecar_json: str,
    resolved_output: str,
    index: int,
    start_dt: datetime,
    end_dt: datetime,
    duration_sec: float,
) -> str:
    """Resolve sidecar path for a spec entry.

    :param sidecar_json: Sidecar option value ('auto' or explicit template path)
    :param resolved_output: Resolved output path for the current spec
    :param index: 1-based segment index
    :param start_dt: Start datetime
    :param end_dt: End datetime
    :param duration_sec: Duration in seconds
    :return: Resolved sidecar file path
    """
    if sidecar_json == "auto":
        return f"{resolved_output}.split-video.json"
    else:
        return _expand_output_template(
            sidecar_json, index, start_dt, end_dt, duration_sec
        )


def _do_main_specs(
    specs: tuple,
    input_path: str,
    output_template: str,
    buffer_before: str | None,
    buffer_after: str | None,
    buffer_policy: str,
    sidecar_json: str | None,
    video_audit_file: str | None,
    raw: bool,
    verbose: bool,
    out_func=print,
) -> int:
    """Process multiple --spec arguments.

    :param specs: Tuple of spec strings
    :param input_path: Path to the input video file
    :param output_template: Output path template (may contain tokens)
    :param buffer_before: Buffer before duration string
    :param buffer_after: Buffer after duration string
    :param buffer_policy: Buffer overflow policy
    :param sidecar_json: Sidecar JSON option ('auto', path template, or None)
    :param video_audit_file: Path to video audit TSV file
    :param raw: Enable raw mode
    :param verbose: Enable verbose output
    :param out_func: Output function
    :return: Number of failures (0 = all succeeded)
    """
    # Validate output template for multiple specs
    if len(specs) > 1 and not _has_template_tokens(output_template):
        raise ValueError(
            "Multiple --spec provided but --output contains no template token. "
            "Add {n} to output path, e.g.: -o output_{n}.mkv"
        )

    if (
        sidecar_json is not None
        and sidecar_json != "auto"
        and len(specs) > 1
        and not _has_template_tokens(sidecar_json)
    ):
        raise ValueError(
            "Multiple --spec provided but --sidecar-json path "
            "contains no template token. "
            "Add {n} to sidecar path, e.g.: --sidecar-json=meta_{n}.json"
        )

    failures = 0
    buf_before_sec = _parse_interval_sec(buffer_before)
    buf_after_sec = _parse_interval_sec(buffer_after)
    bp = BufferPolicy(buffer_policy.lower())

    for idx, spec_str in enumerate(specs, start=1):
        try:
            # A) Parse the spec
            entry = _parse_spec(spec_str)

            # B) Parse start/duration/end
            is_time_only = raw
            sel_start = _parse_ts(entry.start_str, is_time_only)
            sel_duration = (
                _parse_interval_sec(entry.duration_str) if entry.duration_str else None
            )
            sel_end = _parse_ts(entry.end_str, is_time_only) if entry.end_str else None

            # C) Calculate split data
            sd = _calc_split_data(
                input_path,
                sel_start,
                sel_duration,
                sel_end,
                buf_before_sec,
                buf_after_sec,
                bp,
                video_audit_file,
                raw_mode=raw,
            )

            if not sd.success:
                logger.error(
                    f"Spec [{idx}] '{spec_str}': split data calculation failed."
                )
                failures += 1
                continue

            # D) Expand output template
            out_path = _expand_output_template(
                output_template,
                idx,
                sd.sel_seg.start_ts,
                sd.sel_seg.end_ts,
                sd.sel_seg.duration_sec,
            )

            if verbose:
                out_func(f"Spec [{idx}] '{spec_str}' -> {out_path}")

            # E) Run the split
            sr = _split_video(sd, out_path)

            if not sr.success:
                logger.error(f"Spec [{idx}] '{spec_str}': video split failed.")
                failures += 1
                continue

            if verbose:
                out_func(f"  Input path  : {sr.input_path}")
                out_func(f"  Output path : {sr.output_path}")
                out_func(f"  JSON Result : {sr.model_dump_json(indent=2)}")

            # F) Write sidecar JSON
            if sidecar_json is not None:
                sidecar_path = _resolve_sidecar_path(
                    sidecar_json,
                    out_path,
                    idx,
                    sd.sel_seg.start_ts,
                    sd.sel_seg.end_ts,
                    sd.sel_seg.duration_sec,
                )
                _write_sidecar(sidecar_path, sr, verbose, out_func)

        except Exception as e:
            logger.error(f"Spec [{idx}] '{spec_str}': {e}")
            failures += 1
            continue

    return failures


def do_main(
    input_path: str,
    output_path: str,
    start_time: str | None = None,
    duration: str | None = None,
    end_time: str | None = None,
    buffer_before: str | None = None,
    buffer_after: str | None = None,
    buffer_policy: str = "strict",
    sidecar_json: str | None = None,
    video_audit_file: str | None = None,
    raw: bool = False,
    verbose: bool = False,
    specs: tuple = (),
    out_func=print,
) -> int:
    """Main entry point for split_video module.

    Parameters
    ----------
    input_path : str
        Path to the input video file. Filename must contain timestamp in format:
        YYYY.MM.DD.HH.MM.SS.mmm_YYYY.MM.DD.HH.MM.SS.mmm.mkv
    output_path : str
        Path to the output .mkv file. A sidecar .json file will be created
        with the same basename containing metadata.
    start_time : str
        Start time in ISO 8601 format (e.g., '2024-02-02T17:30:00').
    duration : str | None
        Duration of the output video. Accepts seconds (e.g., '180') or
        ISO 8601 duration (e.g., 'P3M' for 3 minutes).
        Mutually exclusive with end_time.
    end_time : str | None
        End time in ISO 8601 format (e.g., '2024-02-02T17:33:00').
        Mutually exclusive with duration.
    buffer_before : str | None
        Duration buffer to include before the start time.
        Accepts seconds (e.g., '10') or ISO 8601 duration (e.g., 'P10S').
    buffer_after : str | None
        Duration buffer to include after the end time.
        Accepts seconds (e.g., '10') or ISO 8601 duration (e.g., 'P10S').
    buffer_policy : str
        Policy for handling buffer overflow: 'strict' (error on overflow) or
        'flexible' (trim buffers to fit). Defaults to 'strict'.
    sidecar_json : str | None
        Path to write sidecar JSON file with split metadata. If None, no sidecar
        file is created.
    video_audit_file : str | None
        Path to video audit TSV file. If provided, uses this file instead of
        generating video metadata on-the-fly. Passed to get_file_video_audit
        as path_tsv parameter.
    raw : bool
        Enable raw mode for video splitting. Defaults to False.
    verbose : bool
        Enable verbose output.
    specs : tuple
        Tuple of --spec argument strings. If non-empty, uses spec mode
        instead of legacy start_time/duration/end_time.
    out_func : callable
        Output function for printing messages.

    Notes
    -----
    - All durations support float seconds or ISO 8601 duration format
    - Precision is milliseconds (ms)
    - Buffers are trimmed if they extend beyond video boundaries
    - If video doesn't overlap with desired time range, an error is raised
    - Multiple videos for a single time range are not supported yet
    - A sidecar .json file is created with metadata including:
      * onset (ISO 8601 time, no date)
      * duration (seconds with ms precision)
      * buffer-before (seconds with ms precision)
      * buffer-after (seconds with ms precision)
      * reprostim-videocapture metadata from the log
    - No absolute dates are stored, only times
    """

    logger.debug("split-video command")
    logger.debug(f"Input path: {input_path}")
    logger.debug(f"Output path: {output_path}")
    logger.debug(f"Specs: {specs}")
    logger.debug(f"Start time: {start_time}")
    logger.debug(f"Duration: {duration}")
    logger.debug(f"End time: {end_time}")
    logger.debug(f"Buffer before: {buffer_before}")
    logger.debug(f"Buffer after: {buffer_after}")
    logger.debug(f"Buffer policy: {buffer_policy}")
    logger.debug(f"Video audit file: {video_audit_file}")
    logger.debug(f"Raw mode: {raw}")

    # If no specs provided, build a synthetic spec from start/duration/end
    if not specs:
        if start_time and duration:
            specs = (f"{start_time}/{duration}",)
        elif start_time and end_time:
            specs = (f"{start_time}//{end_time}",)
        else:
            logger.error(
                "Either --spec or --start with --duration/--end must be provided."
            )
            return 1

    try:
        return _do_main_specs(
            specs=specs,
            input_path=input_path,
            output_template=output_path,
            buffer_before=buffer_before,
            buffer_after=buffer_after,
            buffer_policy=buffer_policy,
            sidecar_json=sidecar_json,
            video_audit_file=video_audit_file,
            raw=raw,
            verbose=verbose,
            out_func=out_func,
        )
    except ValueError as e:
        logger.error(f"Spec validation error: {e}")
        out_func(f"ERROR: {e}")
        return 5
