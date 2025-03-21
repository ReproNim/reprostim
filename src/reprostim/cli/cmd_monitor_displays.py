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
    help="Set display monitoring providers to be used. " "Default is `platform`.",
)
@click.option(
    "-t",
    "--poll-interval",
    default=60,
    type=int,
    help="Specifies displays check/poll interval in seconds "
    "for providers w/o system callbacks.",
)
@click.option(
    "-w",
    "--max-wait",
    default=3,
    type=int,
    help="Specifies maximum wait interval in seconds, " "or -1 to wait forever.",
)
@click.option(
    "-n",
    "--name",
    default="*",
    type=str,
    help="Specifies display name pattern to be monitored"
    " in Unix shell-style wildcards syntax.",
)
@click.option(
    "-i",
    "--id",
    "d_id",
    default="*",
    type=str,
    help="Specifies display ID pattern to be monitored"
    " in Unix shell-style wildcards syntax.",
)
@click.option(
    "-u",
    "--on-change",
    default=None,
    type=str,
    help="Specifies shell script to be executed when target "
    "display is connected, disconnected or monitor "
    "resolution/mode updated.",
)
@click.option(
    "-e",
    "--ext-proc-command",
    default=None,
    type=str,
    help="Specifies external process or shell script to be "
    "executed when target display is connected. "
    "Note: subprocess is automatically terminated when "
    "display is disconnected.",
)
@click.pass_context
def monitor_displays(
    ctx,
    provider: str,
    poll_interval: int,
    max_wait: int,
    name: str,
    d_id: str,
    on_change: str,
    ext_proc_command: str,
):
    """Monitor GUI/displays connection status."""
    logger.debug("reprostim monitor-displays")

    from ..qr.disp_mon import DmProvider, do_monitor_displays

    res: int = 0
    logger.debug("reprostim monitor-displays script started")

    do_monitor_displays(
        DmProvider(provider),
        poll_interval,
        max_wait,
        name,
        d_id,
        on_change,
        ext_proc_command,
    )

    logger.debug(f"reprostim monitor-displays script finished: {res}")
    logger.debug(f"Exit on   : {datetime.now()}")
    logger.debug(f"Exit code : {res}")
    return res
