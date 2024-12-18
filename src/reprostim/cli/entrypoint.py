# SPDX-FileCopyrightText: 2024-present Vadim Melnik <vmelnik@docsultant.com>
#
# SPDX-License-Identifier: MIT
import click
from click_didyoumean import DYMGroup

from ..__about__ import __version__


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(__version__)
    ctx.exit()


# group to provide commands
@click.group(cls=DYMGroup)
@click.version_option(version=__version__, prog_name="reprostim")
@click.option('-l', '--log-level', default='DEBUG',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level.')
@click.pass_context
def main(ctx, log_level):
    pass


# Import all CLI commands
from .cmd_detect_noscreen import detect_noscreen
from .cmd_echo import echo
from .cmd_qr_parse import qr_parse
from .cmd_timesync_stimuli import timesync_stimuli

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



