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

from pydantic import BaseModel, field_validator

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


class MetadataBase(BaseModel):
    """Fields common to every REPROSTIM-METADATA-JSON entry, regardless of
    :class:`MetadataType`.

    All fields are ``Optional[str]`` for now, mirroring the raw JSON as
    written by ``_METADATA_LOG`` in
    ``src/reprostim-capture/videocapture/src/VideoCapture.cpp`` — no
    semantic typing (e.g. parsed timestamps, numeric resolution) yet. Values
    that aren't already JSON strings (``cx``/``cy`` are JSON numbers,
    ``autoRecovery`` is a JSON bool) are coerced to ``str`` on load.
    """

    type: Optional[str] = None  # MetadataType value, e.g. "session_begin"
    version: Optional[str] = None  # reprostim-videocapture version string
    json_ts: Optional[str] = None  # Entry write time (reprostim timestamp format)
    json_isotime: Optional[str] = None  # Entry write time (ISO 8601)
    cap_ts_start: Optional[str] = (
        None  # Capture start time (reprostim timestamp format)
    )
    cap_isotime_start: Optional[str] = None  # Capture start time (ISO 8601)

    @field_validator("*", mode="before")
    @classmethod
    def _stringify(cls, v):
        return None if v is None else str(v)


class MetadataSessionBegin(MetadataBase):
    """``type: session_begin`` — written once when a recording session
    starts."""

    appName: Optional[str] = None  # Capture application name
    serial: Optional[str] = None  # Video capture device serial number
    vDev: Optional[str] = None  # Video capture device name
    aDev: Optional[str] = None  # Audio-in device (ALSA device name)
    cx: Optional[str] = None  # Video frame width in pixels
    cy: Optional[str] = None  # Video frame height in pixels
    frameRate: Optional[str] = None  # Video frame rate
    autoRecovery: Optional[str] = None  # Whether auto-recovery is enabled


class MetadataCaptureStop(MetadataBase):
    """``type: capture_stop`` — written when capture stops."""

    message: Optional[str] = None  # Reason capture stopped
    cap_ts_stop: Optional[str] = None  # Capture stop time (reprostim timestamp format)
    cap_isotime_stop: Optional[str] = None  # Capture stop time (ISO 8601)


class MetadataSessionEnd(MetadataBase):
    """``type: session_end`` — written once the session logger closes,
    after the ffmpeg thread has terminated."""

    message: Optional[str] = None  # Reason the session ended


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
