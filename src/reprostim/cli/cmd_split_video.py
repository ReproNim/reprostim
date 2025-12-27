# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(
    help="Utility to to split recorded video files manually or "
         "based on embedded QR codes."
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
    verbose: bool
):
    """Analyze recorded video files."""

    from ..qr.split_video import do_main

    logger.debug("split_video(...)")
    logger.debug(f"Working dir      : {os.getcwd()}")
    logger.info(f"Verbose output   : {verbose}")

    do_main(verbose, click.echo)
    return 0