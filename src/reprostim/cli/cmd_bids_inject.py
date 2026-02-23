# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os
import time

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(
    help="Inject ReproStim audio/video recordings into a BIDS dataset aligned to scan timing."
)
@click.argument(
    "paths",
    nargs=-1,
    required=True,
    type=click.Path(exists=True),
)
@click.option(
    "-f",
    "--videos",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    required=True,
    help="Path to videos.tsv produced by video-audit. Video file paths in the TSV "
         "are resolved relative to this file's location.",
)
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    default=False,
    help="When a directory is given in PATHS, recurse into subdirectories to find "
         "all *_scans.tsv files.",
)
@click.option(
    "-b",
    "--buffer-before",
    type=str,
    default="0",
    show_default=True,
    help="Extra video to include before scan onset. "
         "Accepts seconds (e.g., '10' or '10.5') or ISO 8601 duration (e.g., 'PT10S').",
)
@click.option(
    "-a",
    "--buffer-after",
    type=str,
    default="0",
    show_default=True,
    help="Extra video to include after scan end. "
         "Accepts seconds (e.g., '10' or '10.5') or ISO 8601 duration (e.g., 'PT10S').",
)
@click.option(
    "-p",
    "--buffer-policy",
    type=click.Choice(["strict", "flexible"], case_sensitive=False),
    default="flexible",
    show_default=True,
    help="Policy for handling buffer overflow beyond video boundaries. "
         "'strict': error if buffers extend beyond video boundaries. "
         "'flexible': trim buffers to fit within video boundaries.",
)
@click.option(
    "-t",
    "--time-offset",
    type=float,
    default=0.0,
    show_default=True,
    help="Clock offset in seconds to add to BIDS scans for security reasons. "
         "Applied after timezone normalization.",
)
@click.option(
    "-q",
    "--qr",
    type=click.Choice(["none", "auto", "embed-existing", "parse"], case_sensitive=False),
    default="none",
    show_default=True,
    help="QR code-based timing refinement mode. "
         "'none': timing based solely on acq_time and --time-offset. "
         "'auto': use QR data if available, fall back to NTP timing. "
         "'embed-existing': use pre-existing parsed QR JSONL files; error if missing. "
         "'parse': run qr-parse on-the-fly on the source video.",
)
@click.option(
    "-l",
    "--layout",
    type=click.Choice(["nearby", "top-stimuli"], case_sensitive=False),
    default="nearby",
    show_default=True,
    help="Output file placement layout within the BIDS dataset. "
         "'nearby': place output next to the corresponding NIfTI in the same datatype folder. "
         "'top-stimuli': place output under a top-level stimuli/ directory mirroring the hierarchy.",
)
@click.option(
    "-z",
    "--timezone",
    type=str,
    default="local",
    show_default=True,
    help="Timezone assumed for ReproStim no-timezone timestamps in videos.tsv. "
         "Use 'local' for the OS system timezone, or an IANA timezone name "
         "(e.g. 'America/New_York', 'UTC') for explicit, reproducible results.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output.",
)
@click.pass_context
def bids_inject(
    ctx,
    paths: tuple,
    videos: str,
    recursive: bool,
    buffer_before: str,
    buffer_after: str,
    buffer_policy: str,
    time_offset: float,
    qr: str,
    layout: str,
    timezone: str,
    verbose: bool,
):
    """Inject ReproStim video recordings into a BIDS dataset.

    PATHS can be one or more of:
    - a _scans.tsv file (processed directly)
    - a session directory (searched for *_scans.tsv files)
    - a dataset/subject root directory (searched recursively with --recursive)
    """

    from ..qr.bids_inject import do_main

    logger.debug("bids_inject(...)")
    logger.debug(f"Working dir    : {os.getcwd()}")
    logger.info(f"PATHS          : {paths}")
    logger.info(f"videos.tsv     : {videos}")
    logger.info(f"Recursive      : {recursive}")
    logger.info(f"Buffer before  : {buffer_before}")
    logger.info(f"Buffer after   : {buffer_after}")
    logger.info(f"Buffer policy  : {buffer_policy}")
    logger.info(f"Time offset    : {time_offset}")
    logger.info(f"QR mode        : {qr}")
    logger.info(f"Layout         : {layout}")
    logger.info(f"Timezone       : {timezone}")
    logger.info(f"Verbose        : {verbose}")

    start_time_sec = time.time()

    res = do_main(
        paths=paths,
        videos_tsv=videos,
        recursive=recursive,
        buffer_before=buffer_before,
        buffer_after=buffer_after,
        buffer_policy=buffer_policy,
        time_offset=time_offset,
        qr=qr,
        layout=layout,
        timezone=timezone,
        verbose=verbose,
        out_func=click.echo,
    )

    elapsed_sec = round(time.time() - start_time_sec, 1)
    logger.debug(f"Command 'bids-inject' completed in {elapsed_sec} sec, exit code {res}")
    if verbose:
        click.echo(f"Command 'bids-inject' completed in {elapsed_sec} sec, exit code {res}")
    return res