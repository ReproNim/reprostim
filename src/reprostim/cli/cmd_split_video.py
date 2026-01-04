# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os
import time

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(
    help="Utility to to split recorded video files manually or "
         "based on embedded QR codes."
)
@click.option(
    "--buffer-before",
    type=str,
    default=None,
    help="Duration buffer to include before the start time. "
         "Accepts seconds (e.g., '10' or '10.5') or ISO 8601 duration (e.g., 'P10S'). "
         "If the buffer extends before the video start, it will be trimmed to 0.",
)
@click.option(
    "--buffer-after",
    type=str,
    default=None,
    help="Duration buffer to include after the end time. "
         "Accepts seconds (e.g., '10' or '10.5') or ISO 8601 duration (e.g., 'P10S'). "
         "If the buffer extends beyond the video end, it will be trimmed to video length.",
)
@click.option(
    "--buffer-policy",
    type=click.Choice(["strict", "flexible"], case_sensitive=False),
    default="strict",
    help="Policy for handling buffer overflow. "
         "'strict' (default): error if buffers extend beyond video boundaries. "
         "'flexible': trim buffers to fit within video boundaries.",
)
@click.option(
    "--start",
    type=str,
    required=True,
    help="Start time in ISO 8601 format (e.g., '2024-02-02T17:30:00'). "
         "Must be within the input video's time range. In raw mode, only time is used "
         "as offset from the start of the video and not the absolute datetime.",
)
@click.option(
    "--duration",
    type=str,
    default=None,
    help="Duration of the output video. "
         "Accepts seconds (e.g., '180' or '180.5') or ISO 8601 duration (e.g., 'P3M' for 3 minutes). "
         "Mutually exclusive with --end.",
)
@click.option(
    "--end",
    type=str,
    default=None,
    help="End time in ISO 8601 format (e.g., '2024-02-02T17:33:00'). "
         "Mutually exclusive with --duration. In raw mode, only time is used "
         "as offset from the start of the video and not the absolute datetime.",
)
@click.option(
    "-i",
    "--input",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
    help="Input video file path. Filename must include timestamp in format: "
         "YYYY.MM.DD.HH.MM.SS.mmm_YYYY.MM.DD.HH.MM.SS.mmm.mkv",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(file_okay=True, dir_okay=False),
    required=True,
    help="Output .mkv file path. A sidecar .json file will be created "
         "with the same basename containing metadata.",
)
@click.option(
    "-j",
    "--sidecar-json",
    default=None,
    required=False,
    help="Create a sidecar JSON file with split metadata. "
         "When specified without a path or 'auto', creates '<output>.split-video.jsonl'. "
         "When specified with a path, uses that path. "
         "If not specified, or specified as 'none', no sidecar file is created.",
)
@click.option(
    "-a",
    "--video-audit-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Path to video audit TSV file. If provided, uses this file instead of "
         "generating video metadata on-the-fly.",
)
@click.option(
    "--raw",
    is_flag=True,
    default=False,
    help="Enable raw mode for video splitting. In this mode any video file can be used as is to "
         "split/crop *.mkv/*.mp4file, utility will work without specific metadata in logs and file name.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output with JSON records.",
)
@click.pass_context
def split_video(
    ctx,
    buffer_before: str | None,
    buffer_after: str | None,
    buffer_policy: str,
    start: str,
    duration: str | None,
    end: str | None,
    input: str,
    output: str,
    sidecar_json: str | None,
    video_audit_file: str | None,
    raw: bool,
    verbose: bool
):
    """Split recorded video files to a specific time range."""

    from ..qr.split_video import do_main

    # Validate mutually exclusive options
    if duration is not None and end is not None:
        raise click.UsageError("--duration and --end are mutually exclusive. Please specify only one.")

    if duration is None and end is None:
        raise click.UsageError("Either --duration or --end must be specified.")

    logger.debug("split_video(...)")
    logger.debug(f"Working dir      : {os.getcwd()}")
    logger.info(f"Input video      : {input}")
    logger.info(f"Output file      : {output}")
    logger.info(f"Start time       : {start}")
    logger.info(f"Duration         : {duration}")
    logger.info(f"End time         : {end}")
    logger.info(f"Buffer before    : {buffer_before}")
    logger.info(f"Buffer after     : {buffer_after}")
    logger.info(f"Buffer policy    : {buffer_policy}")
    logger.info(f"Sidecar JSON     : {sidecar_json}")
    logger.info(f"Video audit file : {video_audit_file}")
    logger.info(f"Raw mode         : {raw}")
    logger.info(f"Verbose output   : {verbose}")

    # Handle automatic sidecar path generation
    sidecar_path = None
    if sidecar_json in { "auto", "" }:
        sidecar_path = f"{output}.split-video.jsonl"
        logger.info(f"Auto sidecar path: {sidecar_path}")
    elif sidecar_json is not None:
        sidecar_path = sidecar_json
    elif sidecar_json is None or sidecar_json == "none":
        sidecar_path = None

    # Record start time
    start_time_sec = time.time()

    res = do_main(
        input_path=input,
        output_path=output,
        start_time=start,
        duration=duration,
        end_time=end,
        buffer_before=buffer_before,
        buffer_after=buffer_after,
        buffer_policy=buffer_policy,
        sidecar_json=sidecar_path,
        video_audit_file=video_audit_file,
        raw=raw,
        verbose=verbose,
        out_func=click.echo
    )

    # Calculate elapsed time
    elapsed_sec = round(time.time() - start_time_sec, 1)
    logger.debug(f"Command 'split-video' completed in {elapsed_sec} sec, exit code {res}")
    if verbose:
        click.echo(f"Command 'split-video' completed in {elapsed_sec} sec, exit code {res}")
    return res