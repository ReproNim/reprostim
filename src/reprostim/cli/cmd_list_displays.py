# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
from datetime import datetime

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(help="List information about available GUI/displays.")
@click.option(
    "-p",
    "--provider",
    default="platform",
    type=click.Choice(["platform", "pygame", "pyglet", "pyudev", "quartz", "randr"]),
    help="Set display monitoring providers to be used",
)
@click.option(
    "-f",
    "--format",
    "fmt",
    default="jsonl",
    type=click.Choice(["jsonl", "text"], case_sensitive=False),
    help="Set the output format",
)
@click.pass_context
def list_displays(ctx, provider: str, fmt: str):
    """List information about available GUI/displays."""
    logger.debug("reprostim list-displays")

    from ..qr.disp_mon import DmProvider, do_list_displays

    res: int = 0
    logger.debug("reprostim list-displays script started")

    do_list_displays(DmProvider(provider), fmt, click.echo)

    logger.debug(f"reprostim list-displays script finished: {res}")
    logger.debug(f"Exit on   : {datetime.now()}")
    logger.debug(f"Exit code : {res}")
    return res
