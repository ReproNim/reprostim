# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
from datetime import datetime

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(help="PsychoPy reprostim list-displays script.")
@click.pass_context
def list_displays(
    ctx,
):
    """List information about available GUI/displays."""
    click.echo("reprostim list-displays")

    res: int = 0
    logger.debug("reprostim list-displays script started")

    logger.debug(f"reprostim list-displays script finished: {res}")
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {res}")
    return res
