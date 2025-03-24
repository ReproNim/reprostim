# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
API to parse `(*.mkv)` video files recorded by `reprostim-videocapture`
utility and extract embeded video media info, QR-codes and audiocodes into
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


# Define class video info details
class InfoSummary(BaseModel):
    path: Optional[str] = Field(None, description="Video file path")
    rate_mbpm: Optional[float] = Field(
        0.0, description="Video file 'byterate' " "in MB per minute."
    )
    duration_sec: Optional[float] = Field(
        0.0, description="Duration of the video " "in seconds"
    )
    size_mb: Optional[float] = Field(0.0, description="Video file size in MB.")


# Define class for video time info
class VideoTimeInfo(BaseModel):
    success: bool = Field(..., description="Success flag")
    error: Optional[str] = Field(None, description="Error message if any")
    start_time: Optional[datetime] = Field(None, description="Start time of the video")
    end_time: Optional[datetime] = Field(None, description="End time of the video")
    duration_sec: Optional[float] = Field(
        None, description="Duration of the video " "in seconds"
    )


# Define model for parsing summary info
class ParseSummary(BaseModel):
    type: Optional[str] = Field("ParseSummary", description="JSON record type/class")
    qr_count: Optional[int] = Field(0, description="Number of QR codes found")
    parsing_duration: Optional[float] = Field(
        0.0, description="Duration of the " "parsing in seconds"
    )
    # exit code
    exit_code: Optional[int] = Field(-1, description="Number of QR codes found")
    video_full_path: Optional[str] = Field(
        None, description="Full path " "to the video file"
    )
    video_file_name: Optional[str] = Field(
        None, description="Name of the " "video file"
    )
    video_isotime_start: Optional[datetime] = Field(
        None, description="ISO datetime " "video started"
    )
    video_isotime_end: Optional[datetime] = Field(
        None, description="ISO datetime " "video ended"
    )
    video_duration: Optional[float] = Field(
        None, description="Duration of the video " "in seconds"
    )
    video_frame_width: Optional[int] = Field(
        None, description="Width of the " "video frame in px"
    )
    video_frame_height: Optional[int] = Field(
        None, description="Height of the " "video frame in px"
    )
    video_frame_rate: Optional[float] = Field(
        None, description="Frame rate of the " "video in FPS"
    )
    video_frame_count: Optional[int] = Field(
        None, description="Number of frames " "in video file"
    )


# Define the data model for the QR record
class QrRecord(BaseModel):
    type: Optional[str] = Field("QrRecord", description="JSON record type/class")
    index: Optional[int] = Field(
        None, description="Zero-based i    ndex of the QR code"
    )
    frame_start: Optional[int] = Field(
        None, description="Frame number where QR code starts"
    )
    frame_end: Optional[int] = Field(
        None, description="Frame number where QR code ends"
    )
    isotime_start: Optional[datetime] = Field(
        None, description="ISO datetime where QR " "code starts"
    )
    isotime_end: Optional[datetime] = Field(
        None, description="ISO datetime where QR " "code ends"
    )
    time_start: Optional[float] = Field(
        None, description="Position in seconds " "where QR code starts"
    )
    time_end: Optional[float] = Field(
        None, description="Position in seconds " "where QR code ends"
    )
    duration: Optional[float] = Field(
        None, description="Duration of the QR code " "in seconds"
    )
    data: Optional[dict] = Field(None, description="QR code data")

    def __str__(self):
        return (
            f"QrRecord(frames=[{self.frame_start}, {self.frame_end}], "
            f"times=[{self.time_start}, {self.time_end} sec], "
            f"duration={self.duration} sec, "
            f"isotimes=[{self.isotime_start}, {self.isotime_end}], "
            f"data={self.data})"
        )


def calc_time(ts: datetime, pos_sec: float) -> datetime:
    return ts + timedelta(seconds=pos_sec)


def get_iso_time(ts: str) -> datetime:
    dt: datetime = datetime.fromisoformat(ts)
    dt = dt.replace(tzinfo=None)
    return dt


def get_video_time_info(path_video: str) -> VideoTimeInfo:
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
