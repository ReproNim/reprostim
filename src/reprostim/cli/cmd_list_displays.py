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
    logger.debug("reprostim list-displays")

    from ..qr.disp_mon import do_list_displays

    res: int = 0
    logger.debug("reprostim list-displays script started")

    do_list_displays()

    logger.debug(f"reprostim list-displays script finished: {res}")
    logger.debug(f"Exit on   : {datetime.now()}")
    logger.debug(f"Exit code : {res}")
    return res
