#!/usr/bin/env python

import logging.config
import os
import subprocess
import sys
import tempfile
import time
from datetime import timedelta
from pydantic import BaseModel, Field
import click
import cv2
import numpy as np

logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)
logger.debug(f"name={__name__}")


class VideoInfo(BaseModel):
    error: str = Field(None, description="Error message")
    fps: float = Field(..., description="Frames per second (FPS)")
    width: int = Field(..., description="Video frame width")
    height: int = Field(..., description="Video frame height")
    is_truncated: bool = Field(False, description="Is video truncated")
    frames_count: int = Field(..., description="Total number of frames")
    nosignal_count: int = Field(..., description="Total number of nosignal "
                                                 "frames")
    nosignal_rate: float = Field(..., description="Rate of nosignal frames "
                                                  "in fraction of total frames")
    scanned_count: int = Field(..., description="Total number of scanned frames")

    def __str__(self):
        return (f"VideoInfo({self.width}x{self.height}, fps={self.fps}, "
                f"frames_count={self.frames_count}, "
                f"scanned_count={self.scanned_count}, "
                f"nosignal_count={self.nosignal_count}, "
                f"nosignal_rate={self.nosignal_rate})"
                )


# Start time
ts = time.time()

# Define the range of colors for the rainbow screen
# This is just an example range, adjust it based on your rainbow screen
lower_rainbow = np.array([0, 50, 50])
upper_rainbow = np.array([30, 255, 255])


def auto_fix_video(video_path: str, temp_path: str):
    logger.info(f"Run mediainfo to get video information: mediainfo -i {video_path}")
    #subprocess.run("echo Run mediainfo", check=True,
    #               shell=True, capture_output=True, text=True)
    #subprocess.run(f"mediainfo -i {video_path}", check=True,
    #               shell=True, capture_output=True, text=True)
    #subprocess.run(["ffmpeg", "-i", video_path, "-c", "copy", temp_path])
    logger.info("TODO: Implement auto-fix for truncated video.")


def has_rainbow(frame):
    # Convert frame to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # Threshold the frame to extract rainbow colors
    mask = cv2.inRange(hsv, lower_rainbow, upper_rainbow)
    # Count non-zero pixels in the mask
    pixel_count = cv2.countNonZero(mask)
    # logger.debug(f"pixel_count={pixel_count}")
    # If a significant number of rainbow pixels are detected, return True
    return pixel_count > 10000  # Adjust threshold as needed


def main_exit(code: int) -> int:
    # print debug message
    exec_time = time.time() - ts
    logger.debug(f"Execution time : {exec_time:.2f} seconds")
    logger.debug(f"Exit code      : {code}")
    sys.exit(code)
    return code


def find_no_signal(video_path: str, step: int = 1,
                   number_of_checks: int = 0,
                   show_progress_sec: float = 0.0) -> VideoInfo:
    vi: VideoInfo = VideoInfo(fps=0, width=0, height=0,
                              is_truncated=False,
                              frames_count=0, nosignal_count=0,
                              nosignal_rate=0.0, scanned_count=0)

    if step < 1:
        vi.error = "Step must be greater than 0";
        return vi

    if number_of_checks < 0:
        vi.error = "Number of checks must be 0 or greater than 0"
        return vi

    if number_of_checks > 0 and step > 1:
        logger.warning(f"Number of checks is set, specified step value({step}) will be ignored.")
        step = 1

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        vi.error = f"Couldn't open the video file: {video_path}"
        return vi

    n1 = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    logger.debug(f"n1={str(n1)}")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.debug(f"frame_count={str(frame_count)}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width: int = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height: int = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vi.width = frame_width
    vi.height = frame_height
    vi.fps = round(fps, 2)
    logger.info(f"Video resolution={frame_width}x{frame_height}, fps={str(fps)}, "
                f"frames count={str(frame_count)}")

    logger.info(f"pos ms={cap.get(cv2.CAP_PROP_POS_MSEC)}, pos frames={cap.get(cv2.CAP_PROP_POS_FRAMES)}")
    nosignal_frames = []

    #    for i in range(frame_count):
    #        logger.debug(f"i={i}")
    #        ret, frame = cap.read()
    #        if not ret:
    #            logger.error(f"Error reading frame {i}")
    #            break
    #
    #        if not has_rainbow(frame):
    #            no_signal_frames.append(i)

    pos_first_frame: int = 0
    pos_last_frame: int = pos_first_frame + frame_count

    if pos_first_frame > pos_last_frame:
        vi.error = f"Invalid frame range: {pos_first_frame} - {pos_last_frame}"
        vi.is_truncated = True
        return vi

    pos_cur_frame: int = pos_first_frame
    pos_next_frame: int = pos_cur_frame
    nosignal_counter: int = 0
    scan_counter: int = 0
    ts_progress: float = time.time()
    progress_interval: float = show_progress_sec
    while True:
        if show_progress_sec > 0.0 and time.time() > ts_progress:
            dt: str = str(timedelta(milliseconds=int(cap.get(cv2.CAP_PROP_POS_MSEC))))
            logger.info(f"Scanning progress: {pos_cur_frame} / {pos_last_frame}, {dt}")
            ts_progress = time.time() + progress_interval

        logger.debug(f"pos_frame={pos_cur_frame}, "
                     f"time={round(pos_cur_frame / fps, 1)}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos_cur_frame)
        ret, frame = cap.read()
        if ret is False:
            logger.debug(f"Failed reading frame {pos_cur_frame}")
            break
        scan_counter += 1

        # set next frame position
        if number_of_checks > 0:
            pos_next_frame = pos_first_frame + int(frame_count * scan_counter / number_of_checks)
        else:
            pos_next_frame = pos_cur_frame + step

        if has_rainbow(frame):
            logger.debug("rainbow-yes")
            nosignal_counter = nosignal_counter + 1
            nosignal_frames.append(pos_cur_frame)
        else:
            logger.debug("rainbow-no")

        pos_cur_frame = pos_next_frame

    logger.debug(f"pos_frame={pos_cur_frame}")
    vi.frames_count = pos_cur_frame
    vi.nosignal_count = nosignal_counter
    vi.scanned_count = scan_counter
    if scan_counter > 0:
        vi.nosignal_rate = round(nosignal_counter / scan_counter, 3)

    cap.release()

    # Calculate time from beginning for each identified frame
    # time_from_beginning = [frame_idx / fps for frame_idx in
    # no_signal_frames]

    return vi


@click.command(help='Utility to determine no-signal frames in '
                    'reprostim-videocapture recorded *.mkv videos.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.option('--step', default=1, type=int,
              help='Specify the step '
                   'for processing '
                   'frames, default is 1.')
@click.option('--number-of-checks', default=0, type=int,
              help='Specify the number '
                   'of checks across entire video'
                   'frames. When set to 0, '
                   'all frames are checked.')
@click.option('--show-progress', default=1.0, type=float,
              help='Specify the interval for showing progress, '
                   'default is 1.0 seconds. When set to 0 or less,'
                   'progress is not shown.')
@click.option('--auto-fix', default=False, is_flag=True,
              help='Automatically fix truncated video when detected'
                   'before nosignal check. Default is False.'
                   'To check if video is truncated, use '
                   'mediainfo -i <video_file> | grep "IsTruncated"')
@click.option('--threshold', default=0.01, type=float,
              help='Specify the threshold for nosignal frames, default is '
                   '0.01 which means 1% of the totally checked frames.')
@click.pass_context
def main(ctx, path: str, log_level, step: int,
         number_of_checks: int,
         show_progress: float,
         auto_fix: bool,
         threshold: float):
    logger.setLevel(log_level)
    logger.debug("nosignal.py tool")

    logger.debug(f"path={path}")

    temp_path: str = None

    res = find_no_signal(path, step, number_of_checks, show_progress)
    if res.is_truncated:
        logger.error(f"ERROR          : Trunctated video detected.")

    if res.is_truncated and auto_fix:
        logger.info("TRUNCATED VIDEO: Attempting to fix the truncated video.")
        temp_path = tempfile.mktemp(suffix="_nosignal_fixed.mkv")
        logger.info(f"Copying video to temporary file: {temp_path}")
        auto_fix_video(path, temp_path)
        res = find_no_signal(temp_path, step, number_of_checks, show_progress)

    if res.error is not None:
        logger.error(f"ERROR          : {res.error}")

    # delete temp_path if exists
    if temp_path is not None and os.path.exists(temp_path):
        logger.info(f"Deleting temporary file: {temp_path}")
        os.remove(temp_path)

    logger.info(f"SCAN RESULT    : {str(res)}")
    if res.nosignal_count > 0 and res.nosignal_rate > threshold:
        click.echo(
            f"FAILED         : {res.nosignal_count} nosignal frames detected "
            f"from {res.scanned_count} scanned ones, "
            f"total frames count {res.frames_count}, "
            f"nosignal rate={res.nosignal_rate * 100}%")
        return main_exit(1)

    click.echo("PASSED         : No nosignal frames detected.")
    return main_exit(0)


if __name__ == "__main__":
    code = main()
