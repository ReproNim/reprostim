# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os

import click
import yaml
from click.core import ParameterSource

# setup logging
logger = logging.getLogger(__name__)


def _load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _apply_config(ctx, config: dict, param_name: str, current_val):
    """Return the config value when the param was not explicitly set on CLI."""
    if ctx.get_parameter_source(param_name) != ParameterSource.DEFAULT:
        return current_val
    key = param_name.replace("_", "-")
    return config.get(key, current_val)


@click.command(
    help="Utility to to analyze video files recorded "
    "by reprostim-videocapture, along with their "
    "corresponding log files and QR/audio metadata."
    "It extracts key information about each "
    "recording and produces a summary table "
    "(videos.tsv) ."
)
@click.argument(
    "paths",
    nargs=-1,  # accept 1 or more arguments
    type=click.Path(exists=True, dir_okay=True, file_okay=True),
)
@click.option(
    "-m",
    "--mode",
    type=click.Choice(
        ["full", "incremental", "force", "rerun-for-na", "reset-to-na"],
        case_sensitive=True,
    ),
    default="incremental",
    show_default=True,
    help=(
        """Specifies operation mode:.

- [full] : regenerate everything from scratch,

- [incremental] : process only new files and merge into existing dataset,

- [force] : redo/update existing records,

- [rerun-for-na] : process only records with N/A values in related fields
                   for external tools like 'nosignal' or 'qr' etc

- [reset-to-na] : set to N/A values in related fields
                   for external tools like 'nosignal' or 'qr' etc

"""
    ),
)
@click.option(
    "-o",
    "--output",
    default="videos.tsv",
    show_default=True,
    type=click.Path(),
    help="Output TSV file to store the video audit summary. "
    "Default is 'videos.tsv' in the current directory.",
)
@click.option(
    "-r",
    "--recursive",
    is_flag=True,
    default=False,
    help="Recursively scan subdirectories for video files.",
)
@click.option(
    "-s",
    "--audit-src",
    multiple=True,
    default=["internal"],
    show_default=True,
    type=click.Choice(["internal", "qr", "nosignal", "all"], case_sensitive=False),
    help=(
        """Specify audit sources: 'internal' for internal checks,
        tool names (e.g., 'qr'), or 'all' to run all:

- [internal] : for internal basic and fast checks,

- [qr] : for QR code based analysis and generating qrinfo files, very slow.

- [nosignal] : to detect no-signal segments in the video in percents, slow.

- [all] : run all available audits.

        Can be used multiple times: -s internal -s qr. Default is 'internal'.
"""
    ),
)
@click.option(
    "-l",
    "--max-files",
    type=int,
    default=-1,
    show_default=True,
    help="Maximum number of video files/records to process. Use -1 for unlimited.",
)
@click.option(
    "-p",
    "--path-mask",
    type=str,
    default=None,
    help="Optional path mask to filter video files based on their paths. Syntax is "
    "the same as used in Python's fnmatch module.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose output with JSON records.",
)
@click.option(
    "-n",
    "--nosignal-opts",
    type=str,
    default=None,
    help=(
        "Override default options passed to detect-noscreen tool. "
        "Provide as a quoted string, e.g. "
        "'--number-of-checks 200 --threshold 0.9'. "
        "If omitted, built-in defaults are used."
    ),
)
@click.option(
    "-q",
    "--qr-opts",
    type=str,
    default=None,
    help=(
        "Additional options to pass to qr-parse tool. "
        "Provide as a quoted string, e.g. '--some-flag value'. "
        "If omitted, no extra options are passed."
    ),
)
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    default=None,
    help=(
        "Optional YAML config file providing defaults for any option not "
        "explicitly set on the CLI. CLI flags always take precedence."
    ),
)
@click.pass_context
def video_audit(
    ctx,
    paths: tuple[str, ...],
    mode: str,
    output: str,
    recursive: bool,
    audit_src,
    max_files: int,
    path_mask: str,
    verbose: bool,
    nosignal_opts: str,
    qr_opts: str,
    config_path: str,
):
    """Analyze recorded video files."""

    from ..qr.video_audit import VaMode, VaSource, do_main

    # load config file and apply as defaults for any param not set on CLI
    config = _load_config(config_path) if config_path else {}
    mode = _apply_config(ctx, config, "mode", mode)
    output = _apply_config(ctx, config, "output", output)
    recursive = _apply_config(ctx, config, "recursive", recursive)
    audit_src = _apply_config(ctx, config, "audit_src", audit_src)
    if isinstance(audit_src, str):
        audit_src = (audit_src,)
    elif isinstance(audit_src, list):
        audit_src = tuple(audit_src)
    max_files = _apply_config(ctx, config, "max_files", max_files)
    path_mask = _apply_config(ctx, config, "path_mask", path_mask)
    verbose = _apply_config(ctx, config, "verbose", verbose)
    nosignal_opts = _apply_config(ctx, config, "nosignal_opts", nosignal_opts)
    qr_opts = _apply_config(ctx, config, "qr_opts", qr_opts)

    logger.debug("video_audit(...)")
    logger.debug(f"Working dir      : {os.getcwd()}")
    if config_path:
        logger.info(f"Config file      : {config_path}")
    logger.info(f"Video full paths : {paths}")
    logger.info(f"Output TSV file  : {output}")
    logger.info(f"Recursive scan   : {recursive}")
    logger.info(f"Operation mode   : {mode}")
    logger.info(f"Audit sources    : {audit_src}")
    logger.info(f"Max files        : {max_files}")
    if path_mask:
        logger.info(f"Path mask        : {path_mask}")
    logger.info(f"Verbose output   : {verbose}")
    if nosignal_opts:
        logger.info(f"Nosignal opts    : {nosignal_opts}")
    if qr_opts:
        logger.info(f"QR opts          : {qr_opts}")

    for path in paths:
        if not os.path.exists(path):
            logger.error(f"Path does not exist: {path}")
            return 1

    do_main(
        list(paths),
        output,
        recursive,
        VaMode(mode),
        {VaSource(s) for s in audit_src},
        max_files,
        path_mask,
        verbose,
        click.echo,
        nosignal_opts=nosignal_opts,
        qr_opts=qr_opts,
    )
    return 0
