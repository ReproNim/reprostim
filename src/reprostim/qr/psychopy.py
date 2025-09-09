# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
API to generate visual QR-codes and audio codes
and embed them into PsychoPy scripts for fMRI experiments
"""
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from time import time
from typing import Any

import qrcode
from psychopy import visual
from pydantic import BaseModel, Field, model_validator

#######################################################
# Constants

#######################################################
# Aux Functions


def get_iso_time(t):
    """Converts a timestamp into an ISO 8601 formatted string
    with local timezone.

    This function takes a timestamp in seconds and converts it into a
    datetime object with local timezone.

    :param t: The timestamp to be converted in seconds.
    :type t: float

    :return: The ISO 8601 formatted string with local timezone.
    :rtype: str
    """
    return datetime.fromtimestamp(t).astimezone().isoformat()


def get_times():
    """Get the current time and its ISO formatted string.

    This function retrieves the current time in seconds since the epoch
    and formats it into an ISO 8601 string with local timezone.

    :return: A tuple containing the current time in seconds and its
             ISO formatted string.
    :rtype: tuple[float, str]
    """
    t = time()
    return t, get_iso_time(t)


def to_json(obj) -> str:
    """Convert an object to a JSON string.

    This function checks if the provided object has a `model_dump_json`
    method (for Pydantic v2) and uses it to convert the object to a JSON
    string. If the method is not available, it falls back to using the
    standard `json.dumps` function.

    :param obj: The object to be converted to a JSON string.
    :type obj: Any

    :return: The JSON string representation of the object.
    :rtype: str
    """
    if hasattr(obj, "model_dump_json"):  # Pydantic v2
        return obj.model_dump_json()
    return json.dumps(obj)


#######################################################
# Classes


# Enum for the event types
class EventType(str, Enum):
    """Enum for known event types for QR code."""

    SESSION_START = "started"  # ?? "session_start"
    """Session start event."""
    SESSION_END = "session_end"
    """Session end event."""
    SERIES_START = "series_begin"  # ?? "series_start"
    """Series start event."""
    SERIES_END = "series_end"
    """Series end event."""
    MRI_TRIGGER_WAITING = "mri_trigger_waiting"
    """Waiting for MRI trigger event."""
    MRI_TRIGGER_RECEIVED = "trigger"  # ?? "mri_trigger_received"
    """MRI trigger received event."""


# original QR code pseudo-data class
def _QrCode_mkrec(**kwargs):
    """Create a basic QR record dictionary."""
    t, tstr = get_times()
    kwargs.update(
        {
            "time": t,
            "time_formatted": tstr,
        }
    )
    return kwargs


class QrCode(dict):
    """Class to hold QR code data. Dict-based QR code record."""

    def __init__(self, event: EventType, **kwargs: Any):
        if not isinstance(event, EventType):
            raise TypeError(f"event must be an EventType, got {type(event)}")

        t, tstr = get_times()
        # Inject mandatory fields
        kwargs.setdefault("time", t)
        kwargs.setdefault("time_formatted", tstr)
        kwargs["event"] = event

        super().__init__(kwargs)

    # Convenience properties
    @property
    def event(self) -> EventType:
        """Type of the event"""
        return self["event"]

    @property
    def time(self) -> float:
        """Time of the event, measured in seconds since the Epoch"""
        return self["time"]

    @property
    def time_formatted(self) -> str:
        """ISO 8601 time of the event"""
        return self["time_formatted"]


class _QrCode_Pydantic(BaseModel):
    """Pydantic model proposal to hold QR code data."""

    event: EventType
    time: float = Field(..., description="Time of the event, seconds since the Epoch")
    time_formatted: str = Field(..., description="ISO 8601 time of the event")

    model_config = {
        "extra": "allow",
        "frozen": False,  # allow assignment
    }

    @model_validator(mode="before")
    @classmethod
    def inject_defaults(cls, data: Any):
        """Inject mandatory fields if missing."""
        if isinstance(data, dict):
            t, tstr = get_times()
            data.setdefault("time", t)
            data.setdefault("time_formatted", tstr)
        return data

    def __getitem__(self, key: str):
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any):
        setattr(self, key, value)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    # Convenience properties (optional, since Pydantic gives direct attr access)
    @property
    def event_type(self) -> EventType:
        return self.event

    @property
    def timestamp(self) -> float:
        return self.time

    @property
    def timestamp_str(self) -> str:
        return self.time_formatted


@dataclass
class QrConfig:
    """Class representing QR and audio codes configuration."""


class QrStim(visual.ImageStim):
    """Class to represent/draw/play QR and audio code stimulus."""

    def __init__(
        self,
        win,
        qr_code: QrCode,
        qr_config: QrConfig = None,
        **kwargs: Any,
    ):
        self.qr_code = qr_code
        self.qr_config = QrConfig() if qr_config is None else qr_config
        super().__init__(win, qrcode.make(to_json(qr_code)), **kwargs)
