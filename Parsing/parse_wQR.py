#!/usr/bin/env python3

import json
import logging
import os

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

record = None

def finalize_record(iframe):
    global record
    record['frame_end'] = iframe
    record['time_end'] = 'TODO'
    print(json.dumps(record), flush=True)
    record = None


def do_parse(path_video: str) -> int:
    starttime = time.time()
    cap = cv2.VideoCapture(path_video)

    # Check if the video opened successfully
    if not cap.isOpened():
        logger.error("Error: Could not open video.")
        return 1

    clips = []
    qrData = {}

    inRun = False

    clip_start = None
    acqNum = None
    runNum = None


    #for f in vid.iter_frames(with_times=True):

    # TODO: just use tqdm for progress indication
    iframe = 0
    global record
    record = None

    while True:
        iframe += 1
        ret, frame = cap.read()
        if not ret:
            break

        f = np.mean(frame, axis=2)  # poor man greyscale from RGB

        if np.mod(iframe,50) == 0:
            print(f"iframe={iframe} {np.std(f)}", file=sys.stderr)

    #    if np.std(f) > 10:
    #        cv2.imwrite('grayscale_image.png', f)
    #        import pdb; pdb.set_trace()

        cod = decode(f, symbols=[ZBarSymbol.QRCODE])
        if len(cod) > 0:
            assert len(cod) == 1, f"Expecting only one, got {len(cod)}"
            data = eval(eval(str(cod[0].data)).decode('utf-8'))
            if record is not None:
                if data == record['data']:
                    # we are still in the same QR code record
                    continue
                # It is a different QR code! we need to finalize current one
                finalize_record(iframe)
            # We just got beginning of the QR code!
            record = {
                'frame_start': iframe,
                'time_start': "TODO-figureout",
                'data' : data
            }
        else:
            if record:
                finalize_record(iframe)

    if record:
        finalize_record(iframe)


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

