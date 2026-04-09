# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
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
from enum import Enum
from pathlib import Path
from typing import Optional

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
        None, description="Video file 'byterate' " "in MB per minute."
    )
    """Video file `byterate` in MB per minute."""
    duration_sec: Optional[float] = Field(
        None, description="Duration of the video " "in seconds"
    )
    """Duration of the video in seconds"""
    size_mb: Optional[float] = Field(None, description="Video file size in MB.")
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


# Define model for parse context/configuration
class Grayscale(str, Enum):
    """Grayscale conversion method applied to each frame before QR decoding."""

    NONE = "none"
    """Pass the raw BGR frame directly — may cause errors with single-channel
    decoders."""

    NUMPY = "numpy"
    """Use ``np.mean(frame, axis=2)`` — legacy, slower (~34 fps)."""

    OPENCV = "opencv"
    """Use ``cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)`` — recommended (~330 fps)."""


class ParseContext(BaseModel):
    """
    Configuration context for the QR parsing process.

    Passed to :func:`do_parse` to control frame processing behaviour.
    Fields are added as new CLI options are implemented.
    """

    grayscale: Grayscale = Field(
        Grayscale.OPENCV,
        description="Grayscale conversion method applied to each frame.",
    )
    scale: float = Field(
        1.0,
        description="Frame downscale factor in (0, 1]. 1.0 = no resize.",
    )
    skip: int = Field(
        0,
        description="Number of frames to skip after each processed frame. "
        "0 = process every frame.",
    )
    std_threshold: float = Field(
        10.0,
        description="Grayscale std-deviation pre-filter threshold. Frames below "
        "this value are skipped before QR decode. 0 or less = disabled.",
    )


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
    pattern1b = r"^(\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3})" r"_\.(mkv|mp4)$"

    # add support for new file format
    pattern2 = (
        r"^(\d{4}\.\d{2}\.\d{2}\-\d{2}\.\d{2}\.\d{2}\.\d{3})"
        r"\-\-(\d{4}\.\d{2}\.\d{2}\-\d{2}\.\d{2}\.\d{2}\.\d{3})\.(mkv|mp4)$"
    )
    pattern2b = (
        r"^(\d{4}\.\d{2}\.\d{2}\-\d{2}\.\d{2}\.\d{2}\.\d{3})" r"\-\-\.(mkv|mp4)$"
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
            # but maybe it is just start time only incomplete file
            match1b: str = re.match(pattern1b, file_name)
            if match1b:
                ts_format = "%Y.%m.%d.%H.%M.%S.%f"
            else:
                match1b = re.match(pattern2b, file_name)
                if match1b:
                    ts_format = "%Y.%m.%d-%H.%M.%S.%f"
                else:
                    return res

            start_ts, extension = match1b.groups()
            try:
                # Parse the timestamps
                res.start_time = datetime.strptime(start_ts, ts_format)
            except ValueError as e:
                res.error = f"Timestamp parsing error: {e}"
                return res

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


def do_info_file(path: str, ignore_errors: bool = False):
    """
    Extracts summary information from a single video file.

    Parses the filename to extract start and end times, computes duration,
    file size, and average data rate in MB per minute.

    :param path: Path to the video file.
    :type path: str

    :param ignore_errors: If True, ignores parsing errors and
                          returns incomplete data. Default is False.

    :return: A tuple containing an InfoSummary object and a
             VideoTimeInfo object.
    """
    logger.info(f"do_info_file({path})")
    vti: VideoTimeInfo = get_video_time_info(path)
    if not vti.success:
        logger.error(f"Failed parse file name time pattern, error: {vti.error}")
        if not ignore_errors:
            return None, vti

    o: InfoSummary = InfoSummary()
    o.path = path
    if vti.duration_sec is not None:
        o.duration_sec = round(vti.duration_sec, 1)
    size: float = os.path.getsize(path)
    o.size_mb = round(size / (1000 * 1000), 1)
    if o.duration_sec is not None and o.duration_sec > 0.0001:
        o.rate_mbpm = round(size * 60 / (o.duration_sec * 1000 * 1000), 1)
    return o, vti


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
        yield do_info_file(path)[0]
    elif p.is_dir():
        logger.info(f"Processing video directory: {path}")
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".mkv"):
                    yield do_info_file(os.path.join(root, file))[0]
            # Uncomment to visit only top-level dir
            # break
    else:
        logger.error(f"Path not found: {path}")


def do_parse(
    ctx: ParseContext,
    path_video: str,
    summary_only: bool = False,
    ignore_errors: bool = False,
):
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

    :param ctx: Parse context holding configuration for frame processing (grayscale
                method, std-threshold, scale, skip, QR decoder, etc.). Initialised
                once by the caller and shared across the entire parse run.
    :type ctx: ParseContext

    :param path_video: Path to the input video file (e.g., `*.mkv`, `*.mp4`).
    :type path_video: str

    :param summary_only: If True, only video metadata summary is returned without
                         parsing for QR codes. Default is False.

    :param ignore_errors: If True, ignores parsing errors and returns incomplete
                          data. Default is False.

    :yield: Individual finalized records (`InfoRecord`) and a final
            `ParseSummary` object.
    :rtype: Generator[Union[InfoRecord, ParseSummary], None, None]
    """
    ps: ParseSummary = ParseSummary()

    vti: VideoTimeInfo = get_video_time_info(path_video)
    if not vti.success:
        logger.error(f"Failed parse file name time pattern, error: {vti.error}")
        if not ignore_errors:
            return

    logger.info(f"Video start time : {vti.start_time}")
    logger.info(f"Video end time   : {vti.end_time}")
    logger.info(
        f"Video duration   : "
        f"{round(vti.duration_sec, 3) if vti.duration_sec is not None else None} sec"
    )

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
    logger.info(f"    - duration   : {round(duration_sec, 3)} sec")
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

    if summary_only:
        ps.exit_code = 0
        ps.parsing_duration = round(time.time() - dt, 1)
        yield ps
        return

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
    parse_fps: float = 0.0
    parse_counter: int = 0
    skip_counter: int = 0

    # remember parse start ts to calculate parse fps
    parse_start_ts: float = time.time()
    # opencv_qr_detector = cv2.QRCodeDetector()
    f_decode: bool = True

    while True:
        iframe += 1
        # pos time in ms
        pos_sec = round((iframe - 1) / fps, 3)
        std_dev = 0.0
        ret, frame = cap.read()
        if not ret:
            break

        # init decode flag
        f_decode = True

        # Handle frame skipping: when skip > 0, only process 1 of every (skip+1) frames
        if ctx.skip > 0:
            if skip_counter > 0:
                skip_counter -= 1
                # logger.debug(f"skip frame {iframe}, skip_counter={skip_counter}")
                # TODO: should we finalize record ???
                continue
            else:
                skip_counter = ctx.skip
                # logger.debug(f"process frame {iframe}, skip_counter={skip_counter}")

        parse_counter += 1

        # logger.debug(f"f.shape={f.shape}, f.dtype={f.dtype}, "
        #              f"f.min={f.min()}, f.max={f.max()}")

        # Apply frame downscaling if requested (before grayscale conversion)
        if ctx.scale != 1.0:
            frame = cv2.resize(
                frame, None, fx=ctx.scale, fy=ctx.scale, interpolation=cv2.INTER_AREA
            )

        # Apply grayscale conversion according to the context configuration if any
        # Note: ? maybe we need to check frame.shape/dtype to decide if we need
        #       to convert or not
        if ctx.grayscale == Grayscale.OPENCV:
            f = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        elif ctx.grayscale == Grayscale.NUMPY:
            f = np.mean(frame, axis=2)
        else:  # Grayscale.NONE
            f = frame

        # Apply std-deviation pre-filter: skip frames unlikely to contain a QR code
        if f_decode and ctx.std_threshold > 0:
            _, std = cv2.meanStdDev(f)
            std_dev = std[0][0]
            if std_dev < ctx.std_threshold:
                # logger.debug(f"Skip frame={iframe} std-threshold: "
                #              f"{std_dev:.2f} < {ctx.std_threshold}")
                f_decode = False

        if np.mod(parse_counter, 50) == 0:
            parse_fps = round(parse_counter / (time.time() - parse_start_ts), 1)
            logger.debug(
                f"iframe={iframe}, std={round(std_dev,1)}, parse_fps={parse_fps} FPS"
            )

        #    if np.std(f) > 10:
        #        cv2.imwrite('grayscale_image.png', f)
        #        import pdb; pdb.set_trace()

        # just for test, check QRCodeDetector().detectAndDecode
        # data, pts, _ = opencv_qr_detector.detectAndDecode(f)
        # data = None
        #
        # if data:
        #    logger.debug(f"OpenCV QRCodeDetector found QR code: {data}, pts={pts}")

        cod = decode(f, symbols=[ZBarSymbol.QRCODE]) if f_decode else ()

        if len(cod) > 0:
            logger.debug(f"Found QR code: {cod}, std={round(std_dev,1)}")
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


def do_main(
    path: str,
    mode: str,
    grayscale: str = Grayscale.OPENCV,
    scale: float = 1.0,
    skip: int = 0,
    std_threshold: float = 10.0,
    out_func=print,
):
    """Entry point for the ``qr-parse`` command.

    Initialises a :class:`ParseContext`, dispatches to :func:`do_parse` or
    :func:`do_info` depending on *mode*, and writes each result to *out_func*.

    :param path: Path to the video file or directory to process.
    :param mode: Execution mode — ``"PARSE"`` or ``"INFO"``.
    :param grayscale: Grayscale conversion method (see :class:`Grayscale`).
    :param scale: Frame downscale factor in ``(0, 1]``; ``1.0`` = no resize.
    :param skip: Frames to skip after each processed frame; ``0`` = process every frame.
    :param std_threshold: Grayscale std-deviation threshold; ``0`` or less = disabled.
    :param out_func: Callable used to emit each output line (default: ``print``).
    :returns: Exit code (``0`` on success, non-zero on error).
    """
    logger.debug("qr-parse command")
    logger.debug(f"Working dir      : {os.getcwd()}")
    logger.info(f"Video full path  : {path}")
    logger.info(f"Grayscale method : {grayscale}")
    logger.info(f"Scale frame      : {scale}")
    logger.info(f"Skip frames      : {skip}")
    logger.info(f"Std threshold    : {std_threshold}")

    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return 1

    if scale <= 0.0 or scale > 1.0:
        logger.error(f"Invalid scale value: {scale}, must be in (0, 1]")
        return 1

    if skip < 0:
        logger.error(f"Invalid skip value: {skip}, must be >= 0")
        return 1

    if mode == "PARSE":
        ctx: ParseContext = ParseContext(
            grayscale=Grayscale(grayscale),
            scale=scale,
            skip=skip,
            std_threshold=std_threshold,
        )
        for item in do_parse(ctx, path):
            out_func(item.model_dump_json())
    elif mode == "INFO":
        for item in do_info(path):
            out_func(item.model_dump_json())
    else:
        logger.error(f"Unknown mode: {mode}")
        return -1
    return 0
