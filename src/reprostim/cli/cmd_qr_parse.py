# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os

import click

from ..qr.qr_parse import do_info, do_parse

# setup logging
logger = logging.getLogger(__name__)


@click.command(help="Utility to parse video and locate integrated " "QR time codes.")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--mode",
    default="PARSE",
    type=click.Choice(["PARSE", "INFO"]),
    help='Specify execution mode. Default is "PARSE", '
    "normal execution. "
    'Use "INFO" to dump video file info like duration, '
    "bitrate, file size etc, (in this case "
    '"path" argument specifies video file or directory '
    "containing video files).",
)
@click.pass_context
def qr_parse(ctx, path: str, mode: str):
    """Parse QR codes in captured videos."""
    logger.debug("qr_parse(...)")
    logger.debug(f"Working dir      : {os.getcwd()}")
    logger.info(f"Video full path  : {path}")

    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return 1

    if mode == "PARSE":
        for item in do_parse(path):
            print(item.model_dump_json())
    elif mode == "INFO":
        for item in do_info(path):
            print(item.model_dump_json())
    else:
        logger.error(f"Unknown mode: {mode}")
    return 0
