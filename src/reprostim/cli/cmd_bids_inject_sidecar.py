# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os
import time

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(
    help="Extract BIDS media-file metadata from audio/video files and "
    "write/update their .json sidecars."
)
@click.argument(
    "files",
    nargs=-1,
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    "-f",
    "--videos",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    default=None,
    help="Optional path to videos.tsv produced by video-audit. When given, "
    "cached fields are looked up for each FILE by resolved path and reused "
    "instead of re-running ffprobe.",
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(["replace", "update"], case_sensitive=False),
    default="update",
    show_default=True,
    help="Sidecar write mode. 'replace': overwrite the entire sidecar with "
    "only the freshly extracted/added fields. 'update': merge freshly "
    "extracted/added fields into the existing sidecar, preserving other "
    "existing keys untouched.",
)
@click.option(
    "-a",
    "--add",
    "add_meta",
    type=str,
    multiple=True,
    help="Manually specify or override a metadata field as META=VALUE. "
    "Repeatable, e.g. --add DeviceSerialNumber=ABC12345 --add "
    "RecordingDuration=3600. Known BIDS fields are cast to their declared "
    "type; unknown fields are stored as strings.",
)
@click.option(
    "-e",
    "--existing-different",
    type=click.Choice(["error", "overwrite"], case_sensitive=False),
    default="error",
    show_default=True,
    help="Policy when a field about to be written already exists in the "
    "sidecar with a different, non-n/a value. 'error': abort processing "
    "that file. 'overwrite': log a warning and proceed with the new value.",
)
@click.option(
    "-d",
    "--dry-run",
    is_flag=True,
    default=False,
    help="Compute and print the field set that would be written per file, "
    "without writing any sidecar.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output.",
)
@click.pass_context
def bids_inject_sidecar(
    ctx,
    files: tuple,
    videos: str,
    mode: str,
    add_meta: tuple,
    existing_different: str,
    dry_run: bool,
    verbose: bool,
):
    """Extract BIDS media-file metadata and write/update sidecars.

    FILES is one or more audio/video files. A .json sidecar is
    written/updated next to each, with the input file's extension
    replaced by ``.json``.
    """

    from ..qr.bids_inject_sidecar import do_main

    logger.debug("bids_inject_sidecar(...)")
    logger.debug(f"Working dir        : {os.getcwd()}")
    logger.info(f"FILES              : {files}")
    logger.info(f"videos.tsv         : {videos}")
    logger.info(f"JSON mode          : {mode}")
    logger.info(f"Add metadata       : {add_meta}")
    logger.info(f"Existing-different : {existing_different}")
    logger.info(f"Dry-run            : {dry_run}")
    logger.info(f"Verbose            : {verbose}")

    start_time_sec = time.time()

    res = do_main(
        files=list(files),
        videos=videos,
        mode=mode,
        add_meta=list(add_meta),
        existing_different=existing_different,
        dry_run=dry_run,
        verbose=verbose,
        out_func=click.echo,
    )

    elapsed_sec = round(time.time() - start_time_sec, 1)
    logger.debug(
        f"Command 'bids-inject-sidecar' completed in {elapsed_sec} sec, "
        f"exit code {res}"
    )
    if verbose:
        click.echo(
            f"Command 'bids-inject-sidecar' completed in {elapsed_sec} sec, "
            f"exit code {res}"
        )
    return res
