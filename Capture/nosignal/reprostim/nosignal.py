import logging.config
import sys
import time
from pydantic import BaseModel, Field
import click
import cv2
import numpy as np

logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)
logger.debug(f"name={__name__}")


class VideoInfo(BaseModel):
    fps: float = Field(..., description="Frames per second (FPS)")
    frames_count: int = Field(..., description="Total number of frames")
    nosignal_count: int = Field(..., description="Total number of nosignal "
                                                 "frames")
    nosignal_rate: float = Field(..., description="Rate of nosignal frames "
                                                  "in fraction of total frames")
    scanned_count: int = Field(..., description="Total number of scanned frames")

    def __str__(self):
        return (f"VideoInfo(fps={self.fps}, "
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


def find_no_signal(video_path: str, step: int = 1) -> VideoInfo:
    if step < 1:
        logger.error("Step must be greater than 0")
        raise ValueError("Step must be greater than 0")

    vi: VideoInfo = VideoInfo(fps=0, frames_count=0, nosignal_count=0,
                              nosignal_rate=0.0, scanned_count=0)
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Couldn't open the video file: {video_path}")
        return

    n1 = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    logger.debug(f"n1={str(n1)}")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.debug(f"frame_count={str(frame_count)}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    vi.fps = round(fps, 2)
    logger.debug(f"fps={str(fps)}")
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

    frame_counter: int = 0
    nosignal_counter: int = 0
    scan_counter: int = 0
    while True:
        logger.debug(f"frame_counter={frame_counter}, "
                     f"time={round(frame_counter / fps, 1)}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_counter)
        ret, frame = cap.read()
        if ret is False:
            logger.debug(f"Failed reading frame {frame_counter}")
            break
        frame_counter += step
        scan_counter += 1

        if has_rainbow(frame):
            logger.debug("rainbow-yes")
            nosignal_counter = nosignal_counter + 1
            nosignal_frames.append(frame_counter)
        else:
            logger.debug("rainbow-no")

    logger.debug(f"frame_counter={frame_counter}")
    vi.frames_count = frame_counter
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
@click.option('--step', default=1, type=int, help='Specify the step '
                                                  'for processing '
                                                  'frames')
@click.option('--threshold', default=0.01, type=float,
              help='Specify the threshold for nosignal frames, default is '
                   '0.01 which means 1% of the total frames.')
@click.pass_context
def main(ctx, path: str, log_level, step: int, threshold: float):
    logger.setLevel(log_level)
    logger.debug("nosignal.py tool")

    logger.debug(f"path={path}")

    res = find_no_signal(path, step)
    logger.info(f"Scan result    : {str(res)}")
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
