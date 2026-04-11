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
import threading
import time
from concurrent.futures import ThreadPoolExecutor
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


class QrDecoder(str, Enum):
    """QR decoding backend."""

    NONE = "none"
    """Disable QR decoding entirely — frame processing (std filter, scaling,
    skipping) still runs, useful for benchmarking or dry-run profiling."""

    OPENCV = "opencv"
    """Use ``cv2.QRCodeDetector().detectAndDecode``."""

    PYZBAR = "pyzbar"
    """Use ``pyzbar.decode`` — default, generally more robust."""


class VideoDecoder(str, Enum):
    """Video frame decoding backend."""

    OPENCV = "opencv"
    """Use ``cv2.VideoCapture`` — default, currently the only supported backend."""


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
    qr_decoder: QrDecoder = Field(
        QrDecoder.PYZBAR,
        description="QR decoding backend. `pyzbar` uses pyzbar.decode (default). "
        "`opencv` uses cv2.QRCodeDetector.detectAndDecode. "
        "`none` disables QR decoding entirely.",
    )
    video_decoder: VideoDecoder = Field(
        VideoDecoder.OPENCV,
        description="Video frame decoding backend. Only `opencv` is supported now; "
        "placeholder for future backends such as `ffmpeg` or `pyav`.",
    )
    qrdet: bool = Field(
        False,
        description="Enable qrdet-based GPU frame pre-filter. When True, a YOLOv8 "
        "QR detector runs on each frame before the full QR decode; frames with no "
        "detected QR region are skipped. Requires `qrdet` and `torch` packages.",
    )
    qrdet_model_size: str = Field(
        "s",
        description="qrdet model size: 'n' (nano), 's' (small), 'm' (medium), "
        "'l' (large). Only used when qrdet=True.",
    )
    qr_decoder_workers: int = Field(
        0,
        description="Number of worker threads for parallel QR decoding. "
        "0 or 1 = sequential (default). N > 1 = parallel with N threads.",
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


# Module-level qrdet detector instance — initialised once in do_main when --qrdet is set.
_qrdet_detector = None


def _init_qrdet(ctx: "ParseContext") -> None:
    """Initialise the module-level ``_qrdet_detector`` when ``ctx.qrdet`` is True.

    Imports ``qrdet`` and ``torch`` lazily.  Raises :exc:`ImportError` with an
    actionable install hint when the packages are missing.

    :param ctx: Parse context — reads ``qrdet`` and ``qrdet_model_size``.
    :raises ImportError: When ``qrdet`` or ``torch`` is not installed.
    """
    global _qrdet_detector
    if not ctx.qrdet:
        _qrdet_detector = None
        return
    try:
        import torch
        from qrdet import QRDetector
    except ImportError as e:
        raise ImportError(
            "The --qrdet pre-filter requires the 'qrdet' and 'torch' packages. "
            "Install them with:  pip install reprostim[gpu]\n"
            f"Original error: {e}"
        ) from e
    _qrdet_detector = QRDetector(model_size=ctx.qrdet_model_size)
    if torch.cuda.is_available():
        _qrdet_detector.model.to("cuda")
    else:
        logger.warning("qrdet: CUDA not available, running on CPU")


def _qrdet_filter(frame) -> bool:
    """Return ``True`` if *frame* should proceed to QR decode.

    Uses the module-level ``_qrdet_detector``.  Returns ``True`` immediately
    when the detector is ``None`` (qrdet disabled).  Otherwise runs the YOLOv8
    region check on the scaled BGR *frame*.

    :param frame: Scaled BGR frame array (before grayscale conversion).
    :returns: ``True`` to proceed with decode, ``False`` to skip the frame.
    """
    if _qrdet_detector is None:
        return True
    detections = _qrdet_detector.detect(image=frame, is_bgr=True)
    return bool(detections)


def _decode_qr_pyzbar(frame) -> Optional[dict]:
    """Decode a QR code from *frame* using ``pyzbar``.

    :param frame: Grayscale frame array.
    :returns: Decoded QR payload as a dict, or ``None`` if no QR code found.
    """
    cod = decode(frame, symbols=[ZBarSymbol.QRCODE])
    if len(cod) == 0:
        return None
    assert len(cod) == 1, f"Expecting only one QR code, got {len(cod)}"
    logger.debug(f"Found QR code (pyzbar): {cod}")
    return eval(eval(str(cod[0].data)).decode("utf-8"))


def _decode_qr_opencv(frame) -> Optional[dict]:
    """Decode a QR code from *frame* using ``cv2.QRCodeDetector``.

    :param frame: Grayscale frame array.
    :returns: Decoded QR payload as a dict, or ``None`` if no QR code found.
    """
    qr_str, _, _ = cv2.QRCodeDetector().detectAndDecode(frame)
    if not qr_str:
        return None
    logger.debug(f"Found QR code (opencv): {qr_str}")
    return eval(qr_str)


def _decode_qr(ctx: ParseContext, frame) -> Optional[dict]:
    """Decode a QR code from *frame* using the backend configured in *ctx*.

    Dispatches to :func:`_decode_qr_pyzbar`, :func:`_decode_qr_opencv`, or
    returns ``None`` immediately when the decoder is ``none``.

    :param ctx: Parse context — selects the QR decoding backend via
                ``ctx.qr_decoder``.
    :param frame: Grayscale (or raw) frame array as returned by the frame
                  processing step in :func:`do_parse`.
    :returns: Decoded QR payload as a dict, or ``None`` if no QR code found.
    """
    if ctx.qr_decoder == QrDecoder.PYZBAR:
        return _decode_qr_pyzbar(frame)
    elif ctx.qr_decoder == QrDecoder.OPENCV:
        return _decode_qr_opencv(frame)
    else:  # QrDecoder.NONE
        return None


def _process_frame(ctx: ParseContext, frame) -> Optional[dict]:
    """Apply scale, grayscale, std-threshold, qrdet pre-filter, and QR decode to *frame*.

    Shared by both the sequential and parallel frame processing paths in
    :func:`do_parse`.

    :returns: Decoded QR payload as a dict, or ``None`` if the frame was
              filtered out or no QR code was found.
    """
    f_decode = False if ctx.qr_decoder == QrDecoder.NONE else True

    # Apply frame downscaling if requested (before grayscale conversion)
    if f_decode and ctx.scale != 1.0:
        frame = cv2.resize(
            frame, None, fx=ctx.scale, fy=ctx.scale, interpolation=cv2.INTER_AREA
        )

    # Apply grayscale conversion according to the context configuration if any
    if f_decode and ctx.grayscale == Grayscale.OPENCV:
        f = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    elif f_decode and ctx.grayscale == Grayscale.NUMPY:
        f = np.mean(frame, axis=2)
    else:  # Grayscale.NONE
        f = frame

    # Apply std-deviation pre-filter: skip frames unlikely to contain a QR code
    if f_decode and ctx.std_threshold > 0:
        _, std = cv2.meanStdDev(f)
        if std[0][0] < ctx.std_threshold:
            f_decode = False

    # Apply qrdet GPU pre-filter: skip frames with no detected QR region
    if f_decode and not _qrdet_filter(frame):
        f_decode = False

    return _decode_qr(ctx, f) if f_decode else None


def _iter_raw_frames(ctx: ParseContext, cap, fps: float):
    """Yield ``(iframe, pos_sec, frame)`` from *cap*, applying skip logic.

    Handles frame-counter bookkeeping and periodic parse-rate logging.
    Shared frame source for both processing paths in :func:`do_parse`.
    """
    iframe = 0
    parse_counter = 0
    skip_counter = 0
    parse_start_ts = time.time()
    while True:
        iframe += 1
        pos_sec = round((iframe - 1) / fps, 3)
        ret, frame = cap.read()
        if not ret:
            break
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
        if np.mod(parse_counter, 50) == 0:
            parse_fps = round(parse_counter / (time.time() - parse_start_ts), 1)
            read_fps = round(iframe / (time.time() - parse_start_ts), 1)
            logger.debug(
                f"iframe={iframe}, read_fps={read_fps}, parse_fps={parse_fps} FPS"
            )
        yield iframe, pos_sec, frame


def _qr_state_machine(ps, vti, results):
    """Run the same/different QR record state machine over *results*.

    Consumes an iterable of ``(iframe, pos_sec, data)`` tuples (where *data*
    is the decoded QR payload dict or ``None``) and yields finalized
    :class:`QrRecord` objects. Works with both lazy generators (sequential
    path) and pre-resolved lists (parallel path).
    """
    record: QrRecord = None
    iframe: int = 0
    pos_sec: float = 0.0
    for iframe, pos_sec, data in results:
        if data is not None:
            logger.debug("Found QR code")
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

    if ctx.qr_decoder_workers > 1:
        # Parallel path: main thread reads frames and submits _process_frame to a
        # thread pool; a semaphore bounds how many frames are in-flight at once.
        sem = threading.Semaphore(ctx.qr_decoder_workers * 4)
        futures: list = []
        with ThreadPoolExecutor(max_workers=ctx.qr_decoder_workers) as executor:
            for iframe, pos_sec, frame in _iter_raw_frames(ctx, cap, fps):
                sem.acquire()
                future = executor.submit(_process_frame, ctx, frame)
                future.add_done_callback(lambda _f: sem.release())
                futures.append((iframe, pos_sec, future))
        # All futures are resolved after the executor context exits.
        # Submission order == iframe order, so no explicit sort needed.
        results = ((ifr, p, fut.result()) for ifr, p, fut in futures)
    else:
        # Sequential path: process each frame immediately as it is read.
        # results is a lazy generator — no buffering.
        results = (
            (ifr, p, _process_frame(ctx, frame))
            for ifr, p, frame in _iter_raw_frames(ctx, cap, fps)
        )

    yield from _qr_state_machine(ps, vti, results)

    ps.exit_code = 0
    ps.parsing_duration = round(time.time() - dt, 1)
    yield ps


def do_main(
    path: str,
    mode: str,
    grayscale: str = Grayscale.OPENCV,
    scale: float = 1.0,
    skip: int = 0,
    std_threshold: float = 10.0,
    qr_decoder: str = QrDecoder.PYZBAR,
    video_decoder: str = VideoDecoder.OPENCV,
    qrdet: bool = False,
    qrdet_model_size: str = "s",
    qr_decoder_workers: int = 0,
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
    :param qr_decoder: QR decoding backend (see :class:`QrDecoder`).
    :param video_decoder: Video frame decoding backend (see :class:`VideoDecoder`).
    :param qrdet: Enable qrdet GPU frame pre-filter.
    :param qrdet_model_size: qrdet model size (``'n'``, ``'s'``, ``'m'``, ``'l'``).
    :param qr_decoder_workers: Worker threads for parallel QR decoding;
    ``0`` or ``1`` = sequential.
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
    logger.info(f"QR decoder       : {qr_decoder}")
    logger.info(f"Video decoder    : {video_decoder}")
    logger.info(f"QRDet pre-filter : {qrdet} (model={qrdet_model_size})")
    logger.info(f"QR decoder workers: {qr_decoder_workers}")

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
            qr_decoder=QrDecoder(qr_decoder),
            video_decoder=VideoDecoder(video_decoder),
            qrdet=qrdet,
            qrdet_model_size=qrdet_model_size,
            qr_decoder_workers=qr_decoder_workers,
        )
        try:
            _init_qrdet(ctx)
        except ImportError as e:
            logger.error(str(e))
            return 1
        for item in do_parse(ctx, path):
            out_func(item.model_dump_json())
    elif mode == "INFO":
        for item in do_info(path):
            out_func(item.model_dump_json())
    else:
        logger.error(f"Unknown mode: {mode}")
        return -1
    return 0
