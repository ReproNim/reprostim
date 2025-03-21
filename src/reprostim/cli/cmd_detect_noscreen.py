# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os
import sys
import tempfile
import time
from importlib.resources import files

import click

# setup logging
logger = logging.getLogger(__name__)

# Start time
ts = time.time()


def _main_exit(code: int) -> int:
    # print debug message
    exec_time = time.time() - ts
    logger.debug(f"Execution time : {exec_time:.2f} seconds")
    logger.debug(f"Exit code      : {code}")
    sys.exit(code)
    return code


@click.command(
    help="Utility to determine no-signal rainbow frames in "
    "`*.mkv` videos recorded by `reprostim-videocapture` tool."
)
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--step",
    default=1,
    type=int,
    help="Specify the step " "for processing " "frames, " "default is 1 frame.",
)
@click.option(
    "--number-of-checks",
    default=0,
    type=int,
    help="Specify the number "
    "of checks across entire video "
    "frames. When set to 0, "
    "all frames are checked.",
)
@click.option(
    "--show-progress",
    default=1.0,
    type=float,
    help="Specify the interval for showing progress, "
    "default is 1.0 seconds. When set to 0 or less, "
    "progress is not shown.",
)
@click.option(
    "--truncated",
    type=click.Choice(["exit2", "fixup", "check5"], case_sensitive=False),
    default="exit2",
    help="\b\nSpecify behavior on truncated video detection. "
    "Default is `exit2`:\n\n"
    "`exit2`  -  exit with error code 2, default value.\n\n"
    "`fixup`  -  use ffmpeg to fix the video by copying "
    "it into a temporary location with command:\n\n"
    "``ffmpeg -i {video_file} -an -c copy {video_fixed}`` \n\n"
    "`check5` - check for nosignal first 5 frames only in "
    "truncated video.\n\n"
    "Note: to check if video is truncated, use command:\n\n"
    '``mediainfo -i <video_file> | grep "IsTruncated"``',
)
@click.option(
    "--invalid-timing",
    type=click.Choice(["exit3", "fixup", "check5"], case_sensitive=False),
    default="exit3",
    help="\b\nSpecify behavior on video with invalid duration:\n \n"
    "`exit3`  - exit with error code 3, default value.\n\n"
    "`fixup`  - use `ffmpeg` to fix the video by copying "
    "it into a temporary location with command:\n\n"
    "``ffmpeg -i {video_file} -an -c copy {video_fixed}``\n\n"
    "`check5` - check for nosignal first 5 frames only in \n"
    "truncated video.",
)
@click.option(
    "--threshold",
    default=0.01,
    type=float,
    help="Specify the threshold for nosignal frames, default is "
    "0.01 which means 1% of the totally checked frames.",
)
@click.pass_context
def detect_noscreen(
    ctx,
    path: str,
    step: int,
    number_of_checks: int,
    show_progress: float,
    truncated: str,
    invalid_timing: str,
    threshold: float,
):
    """Detect no screen/no signal frames in captured videos."""

    from ..capture.nosignal import auto_fix_video, find_no_signal, init_grid_colors

    logger.debug("detect_noscreen(...)")
    logger.debug(f"path={path}")

    temp_path: str = None

    logger.debug("Initializing grid colors...")
    init_grid_colors(files("reprostim") / "assets" / "img" / "nosignal.png")

    res = find_no_signal(path, step, number_of_checks, show_progress, 0)

    if res.error is not None:
        logger.error(str(res.error))

    # process truncated video if any
    if res.is_truncated:
        logger.error("Truncated video detected.")

        if truncated == "exit2":
            return _main_exit(2)

        if truncated == "fixup":
            logger.info("TRUNCATED VIDEO: Attempting to fix the truncated video.")
            temp_path = tempfile.mktemp(suffix="_nosignal_fixed.mkv")
            logger.info(f"Copying video to temporary file: {temp_path}")
            auto_fix_video(path, temp_path)
            res = find_no_signal(temp_path, step, number_of_checks, show_progress, 0)

        if truncated == "check5":
            logger.info("TRUNCATED VIDEO: Checking first 5 frames only.")
            res = find_no_signal(path, step, number_of_checks, show_progress, 5)

    elif res.is_invalid_timing:
        logger.error("Invalid video timing/duration detected.")

        if invalid_timing == "exit3":
            return _main_exit(3)

        if invalid_timing == "fixup":
            logger.info("INVALID TIMING : Attempting to fix the video duration.")
            temp_path = tempfile.mktemp(suffix="_nosignal_fixed.mkv")
            logger.info(f"Copying video to temporary file: {temp_path}")
            auto_fix_video(path, temp_path)
            res = find_no_signal(temp_path, step, number_of_checks, show_progress, 0)

        if invalid_timing == "check5":
            logger.info("INVALID TIMING : Checking first 5 frames only.")
            res = find_no_signal(path, step, number_of_checks, show_progress, 5)

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
            f"nosignal rate={res.nosignal_rate * 100}%"
        )
        return _main_exit(1)

    click.echo("PASSED         : No nosignal frames detected.")
    return _main_exit(0)
