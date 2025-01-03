# SPDX-FileCopyrightText: 2024-present ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import click


@click.command()
@click.argument("message", default="Hello Reprostim World!", required=False)
def echo(message):
    """Echo the provided message or the default value."""
    click.echo(message)
