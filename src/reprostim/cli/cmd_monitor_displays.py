# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
from datetime import datetime

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(help="Monitor GUI/displays connection status.")
@click.option(
    "-p",
    "--provider",
    default="platform",
    type=click.Choice(["platform", "pygame", "pyglet", "pyudev", "quartz", "randr"]),
    help="Set display monitoring providers to be used",
)
@click.pass_context
def monitor_displays(ctx, provider: str):
    """Monitor GUI/displays connection status."""
    logger.debug("reprostim monitor-displays")

    # from ..qr.disp_mon import DmProvider

    res: int = 0
    logger.debug("reprostim monitor-displays script started")

    # TODO: Implement

    logger.debug(f"reprostim monitor-displays script finished: {res}")
    logger.debug(f"Exit on   : {datetime.now()}")
    logger.debug(f"Exit code : {res}")
    return res
