# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(
    help="Utility to to analyze video files recorded "
    "by reprostim-videocapture, along with their "
    "corresponding log files and QR/audio metadata."
    "It extracts key information about each "
    "recording and produces a summary table "
    "(videos.tsv) ."
)
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-m",
    "--mode",
    type=click.Choice(["full", "incremental", "force"], case_sensitive=True),
    default="incremental",
    help=(
        """Specifies operation mode, default is 'incremental' :.

- [full] : regenerate everything from scratch,

- [incremental] : process only new files and merge into existing dataset,

- [force] : redo/update existing records

"""
    ),
)
@click.option(
    "-o",
    "--output",
    default="videos.tsv",
    show_default=True,
    type=click.Path(),
    help="Output TSV file to store the video audit summary. "
    "Default is 'videos.tsv' in the current directory.",
)
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    default=False,
    help="Recursively scan subdirectories for video files.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output with JSON records.",
)
@click.pass_context
def video_audit(ctx, path: str, mode: str, output: str, recursive: bool, verbose: bool):
    """Analyze recorded video files."""

    from ..qr.video_audit import VaMode, do_main

    logger.debug("video_audit(...)")
    logger.debug(f"Working dir      : {os.getcwd()}")
    logger.info(f"Video full path  : {path}")
    logger.info(f"Output TSV file  : {output}")
    logger.info(f"Recursive scan   : {recursive}")
    logger.info(f"Operation mode   : {mode}")
    logger.info(f"Verbose output   : {verbose}")

    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return 1

    do_main(path, output, recursive, VaMode(mode), verbose, click.echo)
    return 0
