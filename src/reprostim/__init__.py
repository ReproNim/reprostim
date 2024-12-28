#
# SPDX-License-Identifier: MIT
import logging
import os
import sys

# setup logging
root_logger = logging.getLogger(__name__)
root_logger.setLevel(logging.NOTSET)


def _init_logger(
    log_level: str,
    log_format: str = "%(asctime)s [%(levelname)s] %(message)s",
    _to_stderr: bool = False,
):
    """Initialize logger with the specified log level."""

    handler = None
    # optionally send all log messages to stderr
    if _to_stderr:
        handler = logging.StreamHandler(sys.stderr)
    else:
        handler = logging.StreamHandler(sys.stdout)

    if handler:
        if log_format:
            formatter = logging.Formatter(log_format)
            handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)

    # set the logging level
    if log_level:
        root_logger.setLevel(log_level)
        # setup log level as environment variable
        # used to setup psychopy logs
        os.environ["REPROSTIM_LOG_LEVEL"] = log_level

    root_logger.debug(f"Logging level set to: {log_level}")
