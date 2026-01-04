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
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import isodate

from pydantic import BaseModel, Field

from reprostim.qr.video_audit import VaRecord, get_file_video_audit

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

    # File info
    path: str = "n/a"  # Path to the .mkv video file
    fps: Optional[float] = None  # Frames per second
    resolution: Optional[str] = None  # Video resolution (e.g., '1920x1080')
    audio_sr: Optional[str] = None  # Audio sample rate (e.g., '48000 Hz')
    full_seg: Optional[VideoSegment] = None   # specifies entire video segment
    sel_seg: Optional[VideoSegment] = None    # specifies exact split video selection
    buf_seg: Optional[VideoSegment] = None    # specifies selection with buffer around


class SplitResult(BaseModel):
    """Specifies result of video split operation."""

    success: bool = Field(False, exclude=True)  # Whether split operation was successful
    input_path: str = Field("n/a", exclude=True)  # Path to the input .mkv video file
    output_path: str = Field("n/a", exclude=True)  # Path to the output .mkv video file
    buffer_before: Optional[float] = None  # Buffer before in seconds
    buffer_after: Optional[float] = None  # Buffer after in seconds
    buffer_start: str = "n/a"  # Start time of the buffer in ISO 8601 format
    buffer_end: str = "n/a" # End time of the buffer in ISO 8601 format
    buffer_duration: Optional[float] = None  # Total buffer duration in seconds
    buffer_offset: Optional[float] = None  # Buffer start offset in seconds
    start: str = "n/a"  # Start time of the split segment only in ISO 8601 format
    start_time: Optional[datetime] = Field(None, exclude=True)  # Start time of the split segment
    end: str = "n/a" # End time of the split segment only in ISO 8601 format
    end_time: Optional[datetime] = Field(None, exclude=True)  # End time of the split segment
    duration: Optional[float] = None  # Duration of the split segment in seconds
    offset: Optional[float] = None  # Offset of the split segment in seconds
    video_resolution: Optional[str] = "n/a"  # Video resolution (e.g., '1920x1080')
    video_rate_fps: Optional[float] = None  # Video frames per second
    video_size_mb: Optional[float] = None  # Video file size in megabytes
    video_rate_mbpm: Optional[float] = None # Video bitrate in megabits per second
    audio_sr: Optional[str] = None  # Audio sample rate (e.g., '48000 Hz')


def _format_time(dt: datetime) -> str:
    """Format datetime object to ISO 8601 time string.

    :param dt: Datetime object
    :type dt: datetime
    :return: Formatted time string in ISO 8601 format (e.g., '17:30:00.321')
    :rtype: str
    """
    return dt.isoformat(timespec='milliseconds').split('T')[1]


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
        if fps_str=="n/a" or not fps_str:
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
        if not interval_str or interval_str=="n/a":
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


def _parse_ts(time_str: str | None) -> datetime:
    """Parse ISO 8601 time string to datetime object.

    :param time_str: Time string in ISO 8601 format
    :type time_str: str
    :return: Parsed datetime object
    :rtype: datetime
    :raises ValueError: If the time string is not in valid format
    """
    try:
        if not time_str:
            return None
        dt = datetime.fromisoformat(time_str)
        return dt
    except ValueError as e:
        logger.error(f"Invalid time format: {time_str}")
        raise e


def _calc_split_data(path: str,
                     sel_start_ts: datetime,
                     sel_duration_sec: float,
                     sel_end_ts: datetime,
                     buf_before_sec: float,
                     buf_after_sec: float,
                     buffer_policy: BufferPolicy = BufferPolicy.STRICT
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

    :return: SplitData object with metadata
    :rtype: SplitData
    :raises ValueError: If buffer cannot be fulfilled in strict mode
    """
    logger.debug(f"_calc_split_data: path={path}, "
                 f"sel_start_ts={sel_start_ts}, sel_duration_sec={sel_duration_sec}, "
                 f"sel_end_ts={sel_end_ts}, buf_before_sec={buf_before_sec}, "
                 f"buf_after_sec={buf_after_sec}, buffer_policy={buffer_policy.value}"
                 )

    sd: SplitData = SplitData(path=path)

    # A) Read video file metadata to get full segment info, fps, frame count etc
    #    as initial implementation use video-audit internal mode
    #    to extract necessary metadata. Later we can optimize it to avoid redundant reads.
    #    and reuse videos.tsv data if any for that.
    vr: VaRecord = get_file_video_audit(path)
    sd.fps = _parse_fps(vr.video_fps_recorded)
    sd.resolution = vr.video_res_recorded
    sd.audio_sr = vr.audio_sr
    sd.full_seg = VideoSegment(
        start_ts=_parse_date_time(vr.start_date, vr.start_time),
        end_ts=_parse_date_time(vr.end_date, vr.end_time),
        offset_sec=0.0,
        offset_frame=0,
        duration_sec=_parse_interval_sec(vr.duration),
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
        raise ValueError(f"Selected start time is before video start: {sd.sel_seg.start_ts} < {sd.full_seg.start_ts}.")

    if sd.sel_seg.end_ts > sd.full_seg.end_ts:
        logger.error("Selected end time is after video end.")
        raise ValueError(f"Selected end time is after video end: {sd.sel_seg.end_ts} > {sd.full_seg.end_ts}.")

    # Handle buffer overflow based on policy
    buffer_overflow_before = sd.buf_seg.start_ts < sd.full_seg.start_ts
    buffer_overflow_after = sd.buf_seg.end_ts > sd.full_seg.end_ts

    if buffer_policy == BufferPolicy.STRICT:
        if buffer_overflow_before:
            logger.error("Buffer before extends before video start (strict mode).")
            raise ValueError(
                f"Buffer before extends before video start: "
                f"buffer_start={sd.buf_seg.start_ts}, video_start={sd.full_seg.start_ts}. "
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
            sd.buf_seg.duration_sec = (sd.buf_seg.end_ts - sd.buf_seg.start_ts).total_seconds()
            sd.buf_seg.frame_count = int(sd.buf_seg.duration_sec * sd.fps)

        if buffer_overflow_after:
            logger.warning("Buffer after extends after video end. Trimming buffer.")
            sd.buf_seg.end_ts = sd.full_seg.end_ts
            sd.buf_seg.duration_sec = (sd.buf_seg.end_ts - sd.buf_seg.start_ts).total_seconds()
            sd.buf_seg.frame_count = int(sd.buf_seg.duration_sec * sd.fps)

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
        buffer_before=round(sd.sel_seg.start_ts.timestamp() - sd.buf_seg.start_ts.timestamp(), 3),
        buffer_after=round(sd.buf_seg.end_ts.timestamp() - sd.sel_seg.end_ts.timestamp(), 3),
        buffer_start=_format_time(sd.buf_seg.start_ts),
        buffer_end=_format_time(sd.buf_seg.end_ts),
        buffer_duration=round(sd.buf_seg.duration_sec, 3),
        buffer_offset=round(sd.buf_seg.offset_sec, 3),
        start_time=sd.sel_seg.start_ts,
        duration=sd.sel_seg.duration_sec,
        offset=sd.sel_seg.offset_sec,
        end_time=sd.sel_seg.end_ts,
        video_resolution=sd.resolution,
        video_rate_fps=sd.fps,
        audio_sr=sd.audio_sr,
    )

    try:
        cmd = [
            "ffmpeg",
            "-y",  # force overwrite
            "-ss", str(sd.buf_seg.offset_sec),
            "-i", sd.path,
            "-t", str(sd.buf_seg.duration_sec),
            "-c", "copy",
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
            sr.video_rate_mbpm = round((file_size_bytes * 8) / (sd.buf_seg.duration_sec * 1024 * 1024), 1)
        sr.success = True
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg error: {e} {e.stdout} {e.stderr}")

    if sr.start_time:
        sr.start = _format_time(sr.start_time)

    if sr.end_time:
        sr.end = _format_time(sr.end_time)

    return sr

def do_main(
        input_path: str,
        output_path: str,
        start_time: str,
        duration: str | None = None,
        end_time: str | None = None,
        buffer_before: str | None = None,
        buffer_after: str | None = None,
        buffer_policy: str = "strict",
        sidecar_json: str | None = None,
        verbose: bool = False,
        out_func=print,
):
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
    verbose : bool
        Enable verbose output.
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
    logger.debug(f"Start time: {start_time}")
    logger.debug(f"Duration: {duration}")
    logger.debug(f"End time: {end_time}")
    logger.debug(f"Buffer before: {buffer_before}")
    logger.debug(f"Buffer after: {buffer_after}")
    logger.debug(f"Buffer policy: {buffer_policy}")

    out_func(f"Slice video from {input_path}")
    out_func(f"  Start: {start_time}, Duration: {duration}, End: {end_time}")
    out_func(f"  Buffers: before={buffer_before}, after={buffer_after}, policy={buffer_policy}")
    out_func(f"  Output: {output_path}")

    sd: SplitData = _calc_split_data(
        input_path,
        _parse_ts(start_time),
        _parse_interval_sec(duration),
        _parse_ts(end_time),
        _parse_interval_sec(buffer_before),
        _parse_interval_sec(buffer_after),
        BufferPolicy(buffer_policy.lower()),
    )
    logger.debug(f"Calculated SplitData: {sd.model_dump_json(indent=2)}")

    sr: SplitResult = _split_video(sd, output_path)
    logger.debug(f"SplitResult: {sr.model_dump_json(indent=2)}")
    out_func(sr.model_dump_json(indent=2))

    # Write sidecar JSON file if requested
    if sidecar_json:
        logger.info(f"Writing sidecar JSON to: {sidecar_json}")
        with open(sidecar_json, 'w') as f:
            f.write(sr.model_dump_json(indent=2))
            f.write('\n')
        logger.debug(f"Sidecar JSON file written successfully")
        out_func(f"Sidecar JSON written to: {sidecar_json}")


