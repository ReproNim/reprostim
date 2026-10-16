# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os

import click
import yaml
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


# name of the YAML config section holding global "reprostim" options,
# all other top-level sections are treated as sub-command names
CONFIG_MAIN_SECTION: str = "reprostim"

# config file locations probed in order when -c/--config is not specified,
# the first existing one is used; relative paths are resolved against the
# current directory, "~" is expanded to the user home directory
DEFAULT_CONFIG_PATHS: tuple[str, ...] = (
    "reprostim_config.yaml",
    ".reprostim/config.yaml",
    "~/.reprostim/config.yaml",
)


def _find_default_config() -> str | None:
    for path in DEFAULT_CONFIG_PATHS:
        path = os.path.expanduser(path)
        if os.path.isfile(path):
            return path
    return None


def _normalize_config_keys(section: dict) -> dict:
    # click looks up defaults by parameter name, so accept both
    # "log-level" and "log_level" spellings in YAML
    return {str(k).replace("-", "_"): v for k, v in section.items()}


def _load_config(path: str) -> dict:
    """Load ReproStim YAML config and convert it to click ``default_map``.

    Expected layout::

        reprostim:          # global options of the main entrypoint
          log-level: DEBUG
        bids-inject:        # optional per sub-command sections
          some-option: value

    :param path: Path to the YAML config file.
    :return: Dict suitable for ``click.Context.default_map``.
    """
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise click.BadParameter(
            f"top-level YAML element must be a mapping in '{path}'",
            param_hint="'-c' / '--config'",
        )

    default_map: dict = {}
    for name, section in data.items():
        if section is None:
            continue
        if not isinstance(section, dict):
            raise click.BadParameter(
                f"section '{name}' must be a mapping in '{path}'",
                param_hint="'-c' / '--config'",
            )
        if name == CONFIG_MAIN_SECTION:
            default_map.update(_normalize_config_keys(section))
        else:
            default_map[str(name)] = _normalize_config_keys(section)
    return default_map


def _config_callback(ctx, param, value):
    # eager option: processed before the others, so populating
    # ctx.default_map here overrides click defaults of the main group
    # options and (via context inheritance) of all sub-commands
    if ctx.resilient_parsing:
        return
    if not value:
        value = _find_default_config()
        if not value:
            return
    default_map = dict(ctx.default_map or {})
    default_map.update(_load_config(value))
    ctx.default_map = default_map
    ctx.meta["reprostim.config"] = value


# group to provide commands
@click.group(cls=DYMGroup)
@click.version_option(version=__version__, prog_name=__reprostim_name__)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    is_eager=True,
    expose_value=False,
    callback=_config_callback,
    help="Path to ReproStim YAML config file to override default option "
    "values. Global options are taken from the 'reprostim' section, "
    "sub-command options from sections named after the sub-command "
    "(e.g. 'bids-inject'). Explicit command-line options take precedence. "
    "If not specified, the first existing of "
    + ", ".join(f"'{p}'" for p in DEFAULT_CONFIG_PATHS)
    + " is used.",
)
@click.option(
    "-l",
    "--log-level",
    default="INFO",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    help="Set the logging level, case-insensitive. Default is INFO.",
)
@click.option(
    "-f",
    "--log-format",
    default="%(asctime)s [%(levelname)s] %(message)s",
    help="Set the logging format string. For the pattern details see standard "
    "Python 'logging.Formatter' documentation.",
)
@click.pass_context
def main(ctx, log_level: str, log_format):
    """Command-line interface to run ReproStim tools and services.
    To see help for the specific command, run:

         reprostim COMMAND --help

    e.g. reprostim timesync-stimuli --help
    """
    # some commands require logging to stderr
    log_to_stderr: bool = ctx.invoked_subcommand in ("qr-parse",)
    _init_logger(log_level.upper(), log_format, log_to_stderr)
    logger.debug(f"{__reprostim_name__} v{__version__}")
    logger.debug(f"main(...), command={ctx.invoked_subcommand}")

    config_path = ctx.meta.get("reprostim.config")
    if config_path:
        logger.debug(f"Found and loaded config yaml: {config_path}")
        for name, section in (ctx.default_map or {}).items():
            if isinstance(section, dict) and name not in main.commands:
                logger.warning(
                    f"Unknown section '{name}' in config '{config_path}', ignored"
                )


# Import all CLI commands
from .cmd_bids_inject import bids_inject  # noqa: E402
from .cmd_bids_inject_sidecar import bids_inject_sidecar  # noqa: E402
from .cmd_detect_noscreen import detect_noscreen  # noqa: E402
from .cmd_echo import echo  # noqa: E402
from .cmd_list_displays import list_displays  # noqa: E402
from .cmd_monitor_displays import monitor_displays  # noqa: E402
from .cmd_qr_parse import qr_parse  # noqa: E402
from .cmd_split_video import split_video  # noqa: E402
from .cmd_timesync_stimuli import timesync_stimuli  # noqa: E402
from .cmd_video_audit import video_audit  # noqa: E402

# List all CLI commands to be included in the main group
__all_commands__ = (
    detect_noscreen,
    echo,
    list_displays,
    monitor_displays,
    qr_parse,
    timesync_stimuli,
    video_audit,
    split_video,
    bids_inject,
    bids_inject_sidecar,
)

# Register all CLI commands
for cmd in __all_commands__:
    main.add_command(cmd)
