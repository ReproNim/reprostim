# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
API to split and audit video files recorded by reprostim-videocapture,
along with their corresponding log files and QR/audio metadata.
"""

import logging

# initialize the logger
# Note: all logs out to stderr
logger = logging.getLogger(__name__)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.debug(f"name={__name__}")


def do_main(
        input_path: str,
        output_path: str,
        start_time: str,
        duration: str | None = None,
        end_time: str | None = None,
        buffer_before: str | None = None,
        buffer_after: str | None = None,
        verbose: bool = False,
        out_func=print,
):
    """Main entry point for split_video module.

    Parameters
    ----------
    input_path : str
        Path to the input video file. Filename must contain timestamp in format:
        YYYY.MM.DD.HH.MM.SS.mmm_YYYY.MM.DD.HH.MM.SS.mmm.mkv
    output_path : str
        Path to the output .mkv file. A sidecar .json file will be created
        with the same basename containing metadata.
    start_time : str
        Start time in ISO 8601 format (e.g., '2024-02-02T17:30:00').
    duration : str | None
        Duration of the output video. Accepts seconds (e.g., '180') or
        ISO 8601 duration (e.g., 'P3M' for 3 minutes).
        Mutually exclusive with end_time.
    end_time : str | None
        End time in ISO 8601 format (e.g., '2024-02-02T17:33:00').
        Mutually exclusive with duration.
    buffer_before : str | None
        Duration buffer to include before the start time.
        Accepts seconds (e.g., '10') or ISO 8601 duration (e.g., 'P10S').
    buffer_after : str | None
        Duration buffer to include after the end time.
        Accepts seconds (e.g., '10') or ISO 8601 duration (e.g., 'P10S').
    verbose : bool
        Enable verbose output.
    out_func : callable
        Output function for printing messages.

    Notes
    -----
    - All durations support float seconds or ISO 8601 duration format
    - Precision is milliseconds (ms)
    - Buffers are trimmed if they extend beyond video boundaries
    - If video doesn't overlap with desired time range, an error is raised
    - Multiple videos for a single time range are not supported yet
    - A sidecar .json file is created with metadata including:
      * onset (ISO 8601 time, no date)
      * duration (seconds with ms precision)
      * buffer-before (seconds with ms precision)
      * buffer-after (seconds with ms precision)
      * reprostim-videocapture metadata from the log
    - No absolute dates are stored, only times
    """

    logger.debug("split-video command")
    logger.debug(f"Input path: {input_path}")
    logger.debug(f"Output path: {output_path}")
    logger.debug(f"Start time: {start_time}")
    logger.debug(f"Duration: {duration}")
    logger.debug(f"End time: {end_time}")
    logger.debug(f"Buffer before: {buffer_before}")
    logger.debug(f"Buffer after: {buffer_after}")

    # TODO: Implement the following:
    # 1. Parse and validate input filename for timestamp pattern
    # 2. Parse start_time, duration/end_time as ISO 8601 formats
    # 3. Parse buffer_before and buffer_after (support both float seconds and ISO 8601)
    # 4. Validate that the requested time range overlaps with the video
    # 5. Calculate actual slice times including buffers (trim to video boundaries)
    # 6. Use ffmpeg to extract the video segment
    # 7. Create sidecar .json file with metadata:
    #    - onset (time only, no date)
    #    - duration (seconds.ms)
    #    - buffer-before (seconds.ms)
    #    - buffer-after (seconds.ms)
    #    - reprostim-videocapture metadata from log
    # 8. Error if video doesn't fully overlap with desired time range
    # 9. Error if multiple videos needed for time range

    out_func("TODO: Implement split-video functionality.")
    out_func(f"Would slice video from {input_path}")
    out_func(f"  Start: {start_time}, Duration: {duration}, End: {end_time}")
    out_func(f"  Buffers: before={buffer_before}, after={buffer_after}")
    out_func(f"  Output: {output_path}")
    pass



