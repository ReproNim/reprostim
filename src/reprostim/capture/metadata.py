# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
API to extract REPROSTIM-METADATA-JSON entries embedded in
reprostim-videocapture log files.

See .ai/capture/metadata-spec.md for the full specification.
"""

import json
import logging
import os
import re
from enum import Enum
from typing import Dict, Generator, Optional

# initialize the logger
# Note: all logs out to stderr
logger = logging.getLogger(__name__)
logger.debug(f"name={__name__}")

# Global REPROSTIM-METADATA-JSON regex pattern
JSON_PATTERN = re.compile(r"REPROSTIM-METADATA-JSON: (.*) :REPROSTIM-METADATA-JSON")


class MetadataType(str, Enum):
    """``type`` field values emitted via ``_METADATA_LOG`` in
    ``src/reprostim-capture/videocapture/src/VideoCapture.cpp``. Keep in sync
    with that file — these are the only three values reprostim-videocapture
    currently writes."""

    SESSION_BEGIN = "session_begin"
    """Emitted once when a recording session starts; carries device/session
    info (``serial``, ``vDev``, ``aDev``, ``cx``, ``cy``, ``frameRate``,
    ``autoRecovery``, ``cap_ts_start``/``cap_isotime_start``)."""
    CAPTURE_STOP = "capture_stop"
    """Emitted when capture stops (``message`` explains why); carries
    ``cap_ts_start``/``cap_isotime_start`` and
    ``cap_ts_stop``/``cap_isotime_stop``."""
    SESSION_END = "session_end"
    """Emitted once when the session logger closes, after the ffmpeg thread
    has terminated; carries ``message`` and
    ``cap_ts_start``/``cap_isotime_start``."""


def iter_metadata_json(log_path: str) -> Generator[Dict, None, None]:
    """
    Iterate over all REPROSTIM-METADATA-JSON lines in the log file.
    Yields parsed JSON dictionaries.

    :param log_path: Path to the log file
    :type log_path: str

    :return: Generator of parsed JSON dictionaries
    :rtype: Generator[Dict, None, None]
    """
    if not os.path.exists(log_path):
        logger.error(f"Log file does not exist: {log_path}")
        return  # file missing, generator yields nothing

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            match = JSON_PATTERN.search(line)
            if match:
                try:
                    data = json.loads(match.group(1))
                    yield data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON in line: {line}")
                    continue


def find_metadata_json(path: str, key: str, value) -> Optional[Dict]:
    """Find the first metadata JSON entry with a specific key-value pair.

    :param path: Path to the log file
    :type path: str

    :param key: Key to search for
    :type key: str

    :param value: Value to match
    :type value: Any

    :return: The first matching dictionary or None if not found
    :rtype: Optional[Dict]
    """
    return next(
        (msg for msg in iter_metadata_json(path) if msg.get(key) == value), None
    )
