# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging

import click
from click_didyoumean import DYMGroup

from .. import _init_logger
from ..__about__ import __reprostim_name__, __version__

# setup logging
logger = logging.getLogger(__name__)


def print_version(ctx, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(__version__)
    ctx.exit()


# group to provide commands
@click.group(cls=DYMGroup)
@click.version_option(version=__version__, prog_name=__reprostim_name__)
@click.option(
    "-l",
    "--log-level",
    default="DEBUG",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set the logging level.",
)
@click.option(
    "-f",
    "--log-format",
    default="%(asctime)s [%(levelname)s] %(message)s",
    help="Set the logging format string. For the pattern details see standard "
    "Python 'logging.Formatter' documentation.",
)
@click.pass_context
def main(ctx, log_level, log_format):
    """Command-line interface to run ReproStim tools and services.
    To see help for the specific command, run:

         reprostim COMMAND --help

    e.g. reprostim timesync-stimuli --help
    """
    # some commands require logging to stderr
    log_to_stderr: bool = ctx.invoked_subcommand in ("qr-parse",)
    _init_logger(log_level, log_format, log_to_stderr)
    logger.debug(f"{__reprostim_name__} v{__version__}")
    logger.debug(f"main(...), command={ctx.invoked_subcommand}")


# Import all CLI commands
from .cmd_detect_noscreen import detect_noscreen  # noqa: E402
from .cmd_echo import echo  # noqa: E402
from .cmd_qr_parse import qr_parse  # noqa: E402
from .cmd_timesync_stimuli import timesync_stimuli  # noqa: E402

# List all CLI commands to be included in the main group
__all_commands__ = (
    detect_noscreen,
    echo,
    qr_parse,
    timesync_stimuli,
)

# Register all CLI commands
for cmd in __all_commands__:
    main.add_command(cmd)
