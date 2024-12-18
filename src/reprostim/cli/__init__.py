# SPDX-FileCopyrightText: 2024-present Vadim Melnik <vmelnik@docsultant.com>
#
# SPDX-License-Identifier: MIT
import click

from reprostim.__about__ import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="reprostim")
def reprostim():
    click.echo("Hello world!")
