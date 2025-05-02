# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
API to parse `(*.mkv)` video files recorded by `reprostim-videocapture`
utility and extract embedded video media info, QR-codes and audiocodes into
JSONL format.
"""

import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click
import cv2
import numpy as np
from pydantic import BaseModel, Field
from pyzbar.pyzbar import ZBarSymbol, decode

# initialize the logger
# Note: all logs out to stderr
logger = logging.getLogger(__name__)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.debug(f"name={__name__}")


class InfoSummary(BaseModel):
    """
    Summary information about a video file.

    Provides video media info details. Contains basic metadata such as
    path, duration, size, and data rate.
    """

    path: Optional[str] = Field(None, description="Video file path")
    """Video file path."""
    rate_mbpm: Optional[float] = Field(
        0.0, description="Video file 'byterate' " "in MB per minute."
    )
    """Video file `byterate` in MB per minute."""
    duration_sec: Optional[float] = Field(
        0.0, description="Duration of the video " "in seconds"
    )
    """Duration of the video in seconds"""
    size_mb: Optional[float] = Field(0.0, description="Video file size in MB.")
    """Video file size in MB."""


# Define class for video time info
class VideoTimeInfo(BaseModel):
    """Metadata for inferred or extracted timing information
    from a video file.

    This model is populated after parsing video filename
    timestamps or media metadata.
    """

    success: bool = Field(..., description="Success flag")
    """Success flag."""
    error: Optional[str] = Field(None, description="Error message if any")
    """Error message if any."""
    start_time: Optional[datetime] = Field(None, description="Start time of the video")
    """Start time of the video."""
    end_time: Optional[datetime] = Field(None, description="End time of the video")
    """End time of the video."""
    duration_sec: Optional[float] = Field(
        None, description="Duration of the video " "in seconds"
    )
    """Duration of the video in seconds."""


# Define model for parsing summary info
class ParseSummary(BaseModel):
    """
    Summary of the QR parsing process and video metadata.

    This model captures information about the parsing results and
    properties of the video being processed.
    """

    type: Optional[str] = Field("ParseSummary", description="JSON record type/class")
    """JSON record type/class."""
    qr_count: Optional[int] = Field(0, description="Number of QR codes found")
    """Number of QR codes found."""
    parsing_duration: Optional[float] = Field(
        0.0, description="Duration of the " "parsing in seconds"
    )
    """Duration of the parsing in seconds."""
    # exit code
    exit_code: Optional[int] = Field(-1, description="Number of QR codes found")
    """Exit code of the parsing process."""
    video_full_path: Optional[str] = Field(
        None, description="Full path " "to the video file"
    )
    """Full path to the video file."""
    video_file_name: Optional[str] = Field(
        None, description="Name of the " "video file"
    )
    """Name of the video file."""
    video_isotime_start: Optional[datetime] = Field(
        None, description="ISO datetime " "video started"
    )
    """ISO datetime when the video started."""
    video_isotime_end: Optional[datetime] = Field(
        None, description="ISO datetime " "video ended"
    )
    """ISO datetime when the video ended."""
    video_duration: Optional[float] = Field(
        None, description="Duration of the video " "in seconds"
    )
    """Duration of the video in seconds."""
    video_frame_width: Optional[int] = Field(
        None, description="Width of the " "video frame in px"
    )
    """Width of the video frame in pixels."""
    video_frame_height: Optional[int] = Field(
        None, description="Height of the " "video frame in px"
    )
    """Height of the video frame in pixels."""
    video_frame_rate: Optional[float] = Field(
        None, description="Frame rate of the " "video in FPS"
    )
    """Frame rate of the video in frames per second."""
    video_frame_count: Optional[int] = Field(
        None, description="Number of frames " "in video file"
    )
    """Number of frames in the video file."""


# Define the data model for the QR record
class QrRecord(BaseModel):
    """
    Represents a decoded QR code segment extracted from a video stream.

    Contains timing, frame location, and content metadata for each detected QR code.
    """

    type: Optional[str] = Field("QrRecord", description="JSON record type/class")
    """JSON record type/class."""
    index: Optional[int] = Field(
        None, description="Zero-based i    ndex of the QR code"
    )
    """Zero-based index of the QR code."""
    frame_start: Optional[int] = Field(
        None, description="Frame number where QR code starts"
    )
    """Frame number where QR code starts."""
    frame_end: Optional[int] = Field(
        None, description="Frame number where QR code ends"
    )
    """Frame number where QR code ends."""
    isotime_start: Optional[datetime] = Field(
        None, description="ISO datetime where QR " "code starts"
    )
    """ISO datetime where QR code starts."""
    isotime_end: Optional[datetime] = Field(
        None, description="ISO datetime where QR " "code ends"
    )
    """ISO datetime where QR code ends."""
    time_start: Optional[float] = Field(
        None, description="Position in seconds " "where QR code starts"
    )
    """Position in seconds where QR code starts."""
    time_end: Optional[float] = Field(
        None, description="Position in seconds " "where QR code ends"
    )
    """Position in seconds where QR code ends."""
    duration: Optional[float] = Field(
        None, description="Duration of the QR code " "in seconds"
    )
    """Duration of the QR code in seconds."""
    data: Optional[dict] = Field(None, description="QR code data")
    """QR code data."""

    def __str__(self):
        return (
            f"QrRecord(frames=[{self.frame_start}, {self.frame_end}], "
            f"times=[{self.time_start}, {self.time_end} sec], "
            f"duration={self.duration} sec, "
            f"isotimes=[{self.isotime_start}, {self.isotime_end}], "
            f"data={self.data})"
        )


def calc_time(ts: datetime, pos_sec: float) -> datetime:
    """
    Calculate a new timestamp by adding seconds to a given datetime.

    :param ts: The original timestamp.
    :type ts: datetime

    :param pos_sec: The number of seconds to add (can be fractional).
    :type pos_sec: float

    :return: The resulting timestamp after adding the specified seconds.
    :rtype: datetime
    """
    return ts + timedelta(seconds=pos_sec)


def get_iso_time(ts: str) -> datetime:
    """
    Parse an ISO 8601 datetime string and return a naive datetime object.

    :param ts: An ISO 8601 formatted datetime string.
    :type ts: str

    :return: A naive datetime object (timezone information is removed).
    :rtype: datetime
    """
    dt: datetime = datetime.fromisoformat(ts)
    dt = dt.replace(tzinfo=None)
    return dt


def get_video_time_info(path_video: str) -> VideoTimeInfo:
    """
    Extract start and end timestamps from a video filename and compute duration.

    The function supports two timestamped filename formats:
    1. `YYYY.MM.DD.HH.MM.SS.mmm_YYYY.MM.DD.HH.MM.SS.mmm.ext`
    2. `YYYY.MM.DD-HH.MM.SS.mmm--YYYY.MM.DD-HH.MM.SS.mmm.ext`

    Valid extensions are `*.mkv` and `*.mp4`.

    :param path_video: Full path to the video file with timestamped filename.
    :type path_video: str

    :return: A VideoTimeInfo object containing success flag, optional error,
             start and end times, and the duration in seconds.
    :rtype: VideoTimeInfo

    :raises ValueError: If timestamps cannot be parsed or are in invalid order.
    """
    res: VideoTimeInfo = VideoTimeInfo(
        success=False, error=None, start_time=None, end_time=None
    )
    # Define the regex pattern for the timestamp and file extension
    # (either .mkv or .mp4)
    pattern1 = (
        r"^(\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3})"
        r"_(\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3})\.(mkv|mp4)$"
    )

    # add support for new file format
    pattern2 = (
        r"^(\d{4}\.\d{2}\.\d{2}\-\d{2}\.\d{2}\.\d{2}\.\d{3})"
        r"\-\-(\d{4}\.\d{2}\.\d{2}\-\d{2}\.\d{2}\.\d{2}\.\d{3})\.(mkv|mp4)$"
    )

    file_name: str = os.path.basename(path_video)
    logger.info(f"Video file name  : {file_name}")

    ts_format = ""
    match1: str = re.match(pattern1, file_name)
    if match1:
        # Define the format for datetime parsing
        ts_format = "%Y.%m.%d.%H.%M.%S.%f"
    else:
        match1 = re.match(pattern2, file_name)
        if match1:
            # Define the format for datetime parsing
            ts_format = "%Y.%m.%d-%H.%M.%S.%f"
        else:
            res.error = f"Filename '{path_video}' does not match the required pattern."
            return res

    start_ts, end_ts, extension = match1.groups()

    try:
        # Parse the timestamps
        res.start_time = datetime.strptime(start_ts, ts_format)
        res.end_time = datetime.strptime(end_ts, ts_format)
    except ValueError as e:
        res.error = f"Timestamp parsing error: {e}"
        return res

    # Validate the chronological order
    if res.start_time >= res.end_time:
        res.error = "Start timestamp is not earlier than end timestamp."
        return res

    # calculate the duration in seconds
    dt: float = (res.end_time - res.start_time).total_seconds()
    res.duration_sec = dt

    res.success = True
    return res


def finalize_record(
    ps: ParseSummary, vti: VideoTimeInfo, record: QrRecord, iframe: int, pos_sec: float
) -> QrRecord:
    """
    Internal API, finalizes the QR code record by setting its
    end time, duration, and index.

    :param ps: parse summary object
    :param vti: video time info object
    :param record: QR code record object
    :param iframe: current frame number
    :param pos_sec: current position in seconds
    :return: QR code record object
    """
    record.frame_end = iframe
    # Note: unclear should we also use last frame duration or not
    record.isotime_end = calc_time(vti.start_time, pos_sec)
    record.time_end = pos_sec
    record.duration = record.time_end - record.time_start
    record.index = ps.qr_count
    logger.info(f"QR: {str(record)}")
    # dump times
    event_time = get_iso_time(record.data["time_formatted"])
    keys_time = get_iso_time(record.data["keys_time_str"])
    logger.info(f" - QR code isotime : {record.isotime_start}")
    logger.info(
        f" - Event isotime   : "
        f"{event_time} / "
        f"dt={(event_time - record.isotime_start).total_seconds()} sec"
    )
    logger.info(
        f" - Keys isotime    : "
        f"{keys_time} / "
        f"dt={(keys_time - record.isotime_start).total_seconds()} sec"
    )
    # print(record.json())
    ps.qr_count += 1
    return record


def do_info_file(path: str):
    """
    Extracts summary information from a single video file.

    Parses the filename to extract start and end times, computes duration,
    file size, and average data rate in MB per minute.

    :param path: Path to the video file.
    :type path: str

    :return: An InfoSummary object with metadata, or None if parsing fails.
    :rtype: InfoSummary or None
    """
    logger.info(f"do_info_file({path})")
    vti: VideoTimeInfo = get_video_time_info(path)
    if not vti.success:
        logger.error(f"Failed parse file name time pattern, error: {vti.error}")
        return
    o: InfoSummary = InfoSummary()
    o.path = path
    o.duration_sec = round(vti.duration_sec, 1)
    size: float = os.path.getsize(path)
    o.size_mb = round(size / (1000 * 1000), 1)
    if o.duration_sec > 0.0001:
        o.rate_mbpm = round(size * 60 / (o.duration_sec * 1000 * 1000), 1)
    return o


def do_info(path: str):
    """
    Yields summary information for a video file or all `*.mkv` files in a directory.

    If the given path is a file, returns its summary.
    If the path is a directory, recursively processes `*.mkv` files within it.

    :param path: Path to a video file or directory containing video files.
    :type path: str

    :yield: InfoSummary object for each video file processed.
    :rtype: Generator[InfoSummary, None, None]
    """
    p = Path(path)
    if p.is_file():
        yield do_info_file(path)
    elif p.is_dir():
        logger.info(f"Processing video directory: {path}")
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".mkv"):
                    yield do_info_file(os.path.join(root, file))
            # Uncomment to visit only top-level dir
            # break
    else:
        logger.error(f"Path not found: {path}")


def do_parse(path_video: str):
    """
    Parse a video file to extract QR code-encoded segments and video metadata.

    The function performs the following steps:
    - Parses the filename to extract start and end timestamps.
    - Extracts video metadata such as resolution, frame rate, frame count, and duration.
    - Iterates through video frames to detect and decode QR codes.
    - Yields finalized records when a QR code is detected or ends.
    - At the end, yields a summary object with parsing stats and video info.

    QR codes are expected to be embedded as visual markers in the video. Each
    QR code corresponds to a data payload which is yielded as a finalized record.

    :param path_video: Path to the input video file (e.g., `*.mkv`, `*.mp4`).
    :type path_video: str

    :yield: Individual finalized records (`InfoRecord`) and a final
            `ParseSummary` object.
    :rtype: Generator[Union[InfoRecord, ParseSummary], None, None]
    """
    ps: ParseSummary = ParseSummary()

    vti: VideoTimeInfo = get_video_time_info(path_video)
    if not vti.success:
        logger.error(f"Failed parse file name time pattern, error: {vti.error}")
        return

    logger.info(f"Video start time : {vti.start_time}")
    logger.info(f"Video end time   : {vti.end_time}")
    logger.info(f"Video duration   : {vti.duration_sec} sec")

    dt = time.time()
    cap = cv2.VideoCapture(path_video)

    # Check if the video opened successfully
    if not cap.isOpened():
        logger.error("Error: Could not open video.")
        return

    # dump video metadata
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width: int = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height: int = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec: float = frame_count / fps if fps > 0 else -1.0
    logger.info("Video media info : ")
    logger.info(f"    - resolution : {frame_width}x{frame_height}")
    logger.info(f"    - frame rate : {str(fps)} FPS")
    logger.info(f"    - duration   : {str(duration_sec)} sec")
    logger.info(f"    - frame count: {str(frame_count)}")
    ps.video_frame_rate = fps
    ps.video_frame_width = frame_width
    ps.video_frame_height = frame_height
    ps.video_frame_count = frame_count
    ps.video_duration = duration_sec
    ps.video_isotime_start = vti.start_time
    ps.video_isotime_end = vti.end_time
    ps.video_full_path = path_video
    ps.video_file_name = os.path.basename(path_video)

    if abs(duration_sec - vti.duration_sec) > 120.0:
        logger.error(
            f"Video duration significant mismatch (real/file name):"
            f" {duration_sec} sec vs {vti.duration_sec} sec"
        )

    # for f in vid.iter_frames(with_times=True):

    # TODO: just use tqdm for progress indication
    iframe: int = 0
    pos_sec: float = 0.0
    record: QrRecord = None

    while True:
        iframe += 1
        # pos time in ms
        pos_sec = round((iframe - 1) / fps, 3)
        ret, frame = cap.read()
        if not ret:
            break

        f = np.mean(frame, axis=2)  # poor man greyscale from RGB

        if np.mod(iframe, 50) == 0:
            logger.debug(f"iframe={iframe} {np.std(f)}")

        #    if np.std(f) > 10:
        #        cv2.imwrite('grayscale_image.png', f)
        #        import pdb; pdb.set_trace()

        cod = decode(f, symbols=[ZBarSymbol.QRCODE])
        if len(cod) > 0:
            logger.debug("Found QR code: " + str(cod))
            assert len(cod) == 1, f"Expecting only one, got {len(cod)}"
            data = eval(eval(str(cod[0].data)).decode("utf-8"))
            if record is not None:
                if data == record.data:
                    # we are still in the same QR code record
                    logger.debug("Same QR code: continue")
                    continue
                # It is a different QR code! we need to finalize current one
                yield finalize_record(ps, vti, record, iframe, pos_sec)
                record = None
            # We just got beginning of the QR code!
            logger.debug("New QR code: " + str(data))
            record = QrRecord()
            record.frame_start = iframe
            record.isotime_start = calc_time(vti.start_time, pos_sec)
            record.isotime_end = None
            record.time_start = pos_sec
            record.data = data
        else:
            if record:
                yield finalize_record(ps, vti, record, iframe, pos_sec)
                record = None

    if record:
        yield finalize_record(ps, vti, record, iframe, pos_sec)
        record = None

    ps.exit_code = 0
    ps.parsing_duration = round(time.time() - dt, 1)
    yield ps
    # print(ps.json())


@click.command(help="Utility to parse video and locate integrated " "QR time codes.")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--mode",
    default="PARSE",
    type=click.Choice(["PARSE", "INFO"]),
    help='Specify execution mode. Default is "PARSE", '
    "normal execution. "
    'Use "INFO" to dump video file info like duration, '
    "bitrate, file size etc, (in this case "
    '"path" argument specifies video file or directory '
    "containing video files).",
)
@click.pass_context
def main(ctx, path: str, mode: str):
    logger.debug("qr-parse command")
    logger.debug(f"Working dir      : {os.getcwd()}")
    logger.info(f"Video full path  : {path}")

    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return 1

    if mode == "PARSE":
        for item in do_parse(path):
            click.echo(item.model_dump_json())
    elif mode == "INFO":
        for item in do_info(path):
            click.echo(item.model_dump_json())
    else:
        logger.error(f"Unknown mode: {mode}")
        return -1
    return 0
