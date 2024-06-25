#!/usr/bin/env python3

import json
import logging
import os
from datetime import datetime

from pydantic import BaseModel, Field
from pyzbar.pyzbar import decode, ZBarSymbol
import cv2
import sys
import numpy as np
import time
import click

# initialize the logger
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)
logger.debug(f"name={__name__}")


# Define class for video time info
class VideoTimeInfo(BaseModel):
    start_time: datetime = Field(..., description="Start time of the video")
    end_time: datetime = Field(..., description="End time of the video")


# Define the data model for the QR record
class QrRecord(BaseModel):
    frame_start: int = Field(..., description="Frame number where QR code starts")
    frame_end: int = Field(None, description="Frame number where QR code ends")
    time_start: str = Field(..., description="Time where QR code starts")
    time_end: str = Field(None, description="Time where QR code ends")
    data: dict = Field(..., description="QR code data")

    def __str__(self):
        return (f"QrRecord(frames=[{self.frame_start}...{self.frame_end}], "
                f"time=[{self.time_start}..{self.time_end}], "
                f"data={self.data})"
                )


def finalize_record(record: QrRecord, iframe: int) -> QrRecord:
    record.frame_end = iframe
    record.time_end = 'TODO'
    logger.info(f"QR: {str(record)}")
    return None


def do_parse(path_video: str) -> int:
    starttime = time.time()
    cap = cv2.VideoCapture(path_video)

    # Check if the video opened successfully
    if not cap.isOpened():
        logger.error("Error: Could not open video.")
        return 1

    # dump video metadata
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width: int = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height: int = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec: float = frame_count / fps if fps > 0 else -1.0
    logger.info(f"Video information: resolution={frame_width}x{frame_height}, fps={str(fps)}, "
                f"frames count={str(frame_count)}, duration={str(duration_sec)} sec")

    clips = []
    qrData = {}

    inRun = False

    clip_start = None
    acqNum = None
    runNum = None

    #for f in vid.iter_frames(with_times=True):

    # TODO: just use tqdm for progress indication
    iframe: int = 0
    record: QrRecord = None

    while True:
        iframe += 1
        ret, frame = cap.read()
        if not ret:
            break

        f = np.mean(frame, axis=2)  # poor man greyscale from RGB

        if np.mod(iframe, 50) == 0:
            logger.info(f"iframe={iframe} {np.std(f)}")

        #    if np.std(f) > 10:
        #        cv2.imwrite('grayscale_image.png', f)
        #        import pdb; pdb.set_trace()

        cod = decode(f, symbols=[ZBarSymbol.QRCODE])
        if len(cod) > 0:
            logger.debug("Found QR code: " + str(cod));
            assert len(cod) == 1, f"Expecting only one, got {len(cod)}"
            data = eval(eval(str(cod[0].data)).decode('utf-8'))
            if record is not None:
                if data == record.data:
                    # we are still in the same QR code record
                    logger.debug(f"Same QR code: continue")
                    continue
                # It is a different QR code! we need to finalize current one
                record = finalize_record(record, iframe)
            # We just got beginning of the QR code!
            logger.debug("New QR code: " + str(data))
            record = QrRecord(frame_start=iframe, frame_end=-1,
                              time_start="TODO-figureout",
                              time_end="",
                              data=data)
        else:
            if record:
                record = finalize_record(record, iframe)

    if record:
        record = finalize_record(record, iframe)


@click.command(help='Utility to parse video and locate integrated '
                    'QR time codes.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.pass_context
def main(ctx, path: str, log_level):
    logger.setLevel(log_level)
    logger.debug("parse_wQR.py tool")
    logger.debug(f"current dir: {os.getcwd()}")
    logger.debug(f"path={path}")

    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return 1

    do_parse(path)
    return 0


if __name__ == "__main__":
    code = main()
    sys.exit(code)
