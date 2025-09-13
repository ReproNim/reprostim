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
@click.pass_context
def video_audit(ctx, path: str):
    """Analyze recorded video files."""

    from ..qr.video_audit import do_main

    logger.debug("video_audit(...)")
    logger.debug(f"Working dir      : {os.getcwd()}")
    logger.info(f"Video full path  : {path}")

    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return 1

    do_main(path, click.echo)
    return 0
