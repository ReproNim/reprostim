# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
Provides functionality to search no-signal/rainbow frames in
the video failes (`*.mkv`) recorded by `reprostim-videocapture`
utility.
"""

import logging.config
import subprocess
import time
from datetime import timedelta

import cv2
import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logger.debug(f"name={__name__}")


class VideoInfo(BaseModel):
    error: str = Field(None, description="Error message")
    fps: float = Field(..., description="Frames per second (FPS)")
    width: int = Field(..., description="Video frame width")
    height: int = Field(..., description="Video frame height")
    is_invalid_timing: bool = Field(
        False, description="Is video with invalid duration/timing"
    )
    is_truncated: bool = Field(False, description="Is video truncated")
    frames_count: int = Field(..., description="Total number of frames")
    nosignal_count: int = Field(..., description="Total number of nosignal " "frames")
    nosignal_rate: float = Field(
        ..., description="Rate of nosignal frames " "in fraction of total frames"
    )
    scanned_count: int = Field(..., description="Total number of scanned frames")

    def __str__(self):
        return (
            f"VideoInfo({self.width}x{self.height}, fps={self.fps}, "
            f"is_truncated={self.is_truncated}, "
            f"frames_count={self.frames_count}, "
            f"scanned_count={self.scanned_count}, "
            f"nosignal_count={self.nosignal_count}, "
            f"nosignal_rate={self.nosignal_rate})"
        )


# Define the range of colors for the rainbow screen
# This is just an example range, adjust it based on your rainbow screen
lower_rainbow = np.array([0, 50, 50])
upper_rainbow = np.array([30, 255, 255])

# Specify nosignal grid size (8 bands) for custom algorithm
grid_rows: int = 6
grid_cols: int = 8
grid_colors = [[None for _ in range(grid_cols)] for _ in range(grid_rows)]


def auto_fix_video(video_path: str, temp_path: str):
    logger.info(f"Run mediainfo to get video information: mediainfo -i {video_path}")
    res = subprocess.run(
        f"mediainfo -i {video_path}",
        check=True,
        shell=True,
        capture_output=True,
        text=True,
    )
    logger.info(f"[exit code] : {res.returncode}")
    logger.info(f"[stdout]    : {res.stdout}")
    logger.info(f"[stderr]    : {res.stderr}")

    logger.info(f"Run fixup ffmpeg : ffmpeg -i {video_path} -an -c copy {temp_path}")
    res = subprocess.run(
        f"ffmpeg -i {video_path} -c copy {temp_path}",
        check=True,
        shell=True,
        capture_output=True,
        text=True,
    )
    logger.info(f"[exit code] : {res.returncode}")
    logger.info(f"[stdout]    : {res.stdout}")
    logger.info(f"[stderr]    : {res.stderr}")
    logger.info("Video fixup completed.")


# Function to calculate opencv2 color difference
def calc_color_diff(color1, color2):
    b1, g1, r1 = color1.astype(np.int32)
    b2, g2, r2 = color2.astype(np.int32)
    return abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)


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


# match nosignal grid colors using custom algorithm
# based on reference image sample
def has_rainbow2(frame):
    height, width, _ = frame.shape
    cy = height // grid_rows
    cx = width // grid_cols
    n = grid_rows * grid_cols
    diff = 0
    for i in range(grid_rows):
        for j in range(grid_cols):
            x = int(j * cx + cx // 2)
            y = int(i * cy + cy // 2)
            clr1 = grid_colors[i][j]
            clr2 = frame[y, x]
            diff = diff + calc_color_diff(clr1, clr2)

    diff = diff / n
    logger.debug(f"diff={diff}")
    # NOTE: tune the threshold value as needed
    return diff < 35


def init_grid_colors(ref_image_path: str):
    logger.debug(f"ref_image_path={ref_image_path}")

    # Load reference image
    image = cv2.imread(ref_image_path)

    # Get the dimensions of the image
    height, width, _ = image.shape

    # Calculate the height and width of grid cell
    cell_height = height // grid_rows
    cell_width = width // grid_cols

    # Loop over the grid
    for i in range(grid_rows):
        for j in range(grid_cols):
            # Calculate the center of each region
            x = int(j * cell_width + cell_width // 2)
            y = int(i * cell_height + cell_height // 2)

            # Get the pixel color at the center
            # opencv use (row, column) coordinates
            clr = image[y, x]

            # Store the color in the 2D list
            grid_colors[i][j] = clr

    # dump the grid colors
    logger.debug("Nosignal reference grid colors:")
    for i, row in enumerate(grid_colors):
        for j, color in enumerate(row):
            b, g, r = color.astype(np.int32)  # OpenCV stores colors as BGR
            logger.debug(f" grid_colors[{i+1}, {j+1}] : RGB({r}, {g}, {b})")


def find_no_signal(
    video_path: str,
    step: int = 1,
    number_of_checks: int = 0,
    show_progress_sec: float = 0.0,
    check_first_frames: int = 0,
) -> VideoInfo:
    vi: VideoInfo = VideoInfo(
        fps=0,
        width=0,
        height=0,
        is_invalid_timing=False,
        is_truncated=False,
        frames_count=0,
        nosignal_count=0,
        nosignal_rate=0.0,
        scanned_count=0,
    )

    if step < 1:
        vi.error = "Step must be greater than 0"
        return vi

    if check_first_frames > 0 and number_of_checks > 0:
        logger.warning(
            f"check_first_frames value specified, "
            f"ignore number_of_checks({number_of_checks}) value."
        )
        number_of_checks = 0

    if number_of_checks < 0:
        vi.error = "Number of checks must be 0 or greater than 0"
        return vi

    if number_of_checks > 0 and step > 1:
        logger.warning(
            f"Number of checks is set, specified step value({step}) will be ignored."
        )
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
    duration_sec: float = frame_count / fps if fps > 0 else -1.0
    logger.debug(f"duration_sec={duration_sec}")
    vi.width = frame_width
    vi.height = frame_height
    vi.fps = round(fps, 2)
    logger.info(
        f"Video resolution={frame_width}x{frame_height}, fps={str(fps)}, "
        f"frames count={str(frame_count)}"
    )

    logger.info(
        f"pos ms={cap.get(cv2.CAP_PROP_POS_MSEC)}, "
        f"pos frames={cap.get(cv2.CAP_PROP_POS_FRAMES)}"
    )
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
        vi.is_truncated = True
        if check_first_frames == 0:
            vi.error = f"Invalid frame range: {pos_first_frame} - {pos_last_frame}"
            return vi

    if duration_sec < 0 or duration_sec > 2 * 24 * 60 * 60:
        vi.is_invalid_timing = True
        if check_first_frames == 0:
            vi.error = f"Invalid video duration: {duration_sec} seconds"
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

        logger.debug(
            f"pos_frame={pos_cur_frame}, " f"time={round(pos_cur_frame / fps, 1)}"
        )
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos_cur_frame)
        ret, frame = cap.read()
        if ret is False:
            logger.debug(f"Failed reading frame {pos_cur_frame}")
            break

        # for some rare videos, opencv continues to read frames even
        # after the end of video
        # e.g. Videos/2024/03/2024.03.18.14.39.38.336_2024.03.18.14.44.02.541.mkv
        # to fix this cases, just break the loop
        if pos_cur_frame > pos_last_frame:
            logger.debug(
                f"Failed reading frame sequencer, "
                f"pos_cur_frame={pos_cur_frame} > "
                f"pos_last_frame={pos_last_frame}"
            )
            break

        # also double check number_of_checks for similar cases
        if 0 < number_of_checks <= scan_counter:
            logger.debug(
                f"Failed reading frame, number_of_checks={number_of_checks} "
                f"limit reached"
            )
            break

        scan_counter += 1

        # break if check_first_frames is set and reached
        if check_first_frames > 0 and scan_counter >= check_first_frames:
            logger.debug(f"check_first_frames={check_first_frames} reached")
            break

        # set next frame position
        if number_of_checks > 0:
            pos_next_frame = pos_first_frame + int(
                frame_count * scan_counter / number_of_checks
            )
        else:
            pos_next_frame = pos_cur_frame + step

        if has_rainbow2(frame):
            logger.debug("rainbow-yes")
            nosignal_counter = nosignal_counter + 1
            nosignal_frames.append(pos_cur_frame)
        else:
            logger.debug("rainbow-no")

        pos_cur_frame = pos_next_frame

    logger.debug(f"pos_frame={pos_cur_frame}")
    vi.frames_count = scan_counter if vi.is_truncated else pos_cur_frame
    vi.nosignal_count = nosignal_counter
    vi.scanned_count = scan_counter
    if scan_counter > 0:
        vi.nosignal_rate = round(nosignal_counter / scan_counter, 3)

    cap.release()

    # Calculate time from beginning for each identified frame
    # time_from_beginning = [frame_idx / fps for frame_idx in
    # no_signal_frames]

    return vi
