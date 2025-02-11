# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

# Display monitoring service: cross-platform API to list
# available GUI displays and monitor status

import json
import logging
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Generator

# initialize the logger
logger = logging.getLogger(__name__)
# logging.getLogger().setLevel(logging.DEBUG)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logger.debug(f"name={__name__}")


# Service provider constants
class DmProvider(str, Enum):
    """Enum to represent the display monitoring provider/engine
    depending on used OS environment."""

    PYUDEV = "pyudev"  # Used in Linux
    QUARTZ = "quartz"  # Used in macOS


# import necessary provider implementation in runtime based on OS type
if sys.platform.startswith("linux"):
    _PROVIDER = DmProvider.PYUDEV
elif sys.platform == "darwin":
    import Quartz

    _PROVIDER = DmProvider.QUARTZ
else:
    logger.error(f"Unsupported OS: {sys.platform}")
    raise NotImplementedError(f"Unsupported OS: {sys.platform}")

logger.debug(f"Use '{_PROVIDER}' provider.")

MAX_DISPLAYS: int = 16


# class representing display info
@dataclass
class DisplayInfo:
    id: int = 0
    name: str = None
    width: int = 0
    height: int = 0
    refresh_rate: float = 0.0
    bits_per_pixel: int = 0
    is_connected: bool = False
    is_active: bool = False
    is_main: bool = False
    is_sleeping: bool = False


# pyudev implementation
def _enum_displays_pyudev():
    pass


# quartz implementation
def _enum_displays_quartz() -> Generator[DisplayInfo, None, None]:
    # logger.debug(dir(Quartz))

    main_id = Quartz.CGMainDisplayID()
    logger.debug(f"main_id={main_id}")

    (e, lst_ids, c) = Quartz.CGGetOnlineDisplayList(MAX_DISPLAYS, None, None)
    if e:
        logger.error(f"Quartz.CGGetOnlineDisplayList() failed: {e}")
        return

    logger.debug(f"online displays count : {c}")
    logger.debug(f"online displays: {lst_ids}")

    for d_id in lst_ids:
        logger.debug(f"display id={d_id}")
        di: DisplayInfo = DisplayInfo()
        di.id = d_id
        vendor_id = Quartz.CGDisplayVendorNumber(d_id)
        model_id = Quartz.CGDisplayModelNumber(d_id)
        serial_id = Quartz.CGDisplaySerialNumber(d_id)
        di.name = f"{vendor_id},{model_id},{serial_id}"  # TODO expand IDs
        di.width = Quartz.CGDisplayPixelsWide(d_id)
        di.height = Quartz.CGDisplayPixelsHigh(d_id)
        di.bits_per_pixel = Quartz.CGDisplayBitsPerPixel(d_id)
        di.is_connected = True
        di.is_active = bool(Quartz.CGDisplayIsActive(d_id))
        di.is_main = d_id == main_id
        di.is_sleeping = bool(Quartz.CGDisplayIsAsleep(d_id))

        # extract additional info, but it should be released
        dm = Quartz.CGDisplayCopyDisplayMode(d_id)
        if dm:
            try:
                di.refresh_rate = Quartz.CGDisplayModeGetRefreshRate(dm)
                # di.bits_per_pixel = Quartz.CGDisplayModeCopyPixelEncoding(dm)
            finally:
                Quartz.CGDisplayModeRelease(dm)

        yield di


def enum_displays() -> Generator[DisplayInfo, None, None]:
    if _PROVIDER == DmProvider.QUARTZ:
        return _enum_displays_quartz()
    elif _PROVIDER == DmProvider.PYUDEV:
        return _enum_displays_pyudev()
    else:
        raise NotImplementedError(f"Unsupported OS: {sys.platform}")


def do_list_displays():
    logger.debug("do_list_displays()")
    for di in enum_displays():
        print(json.dumps(asdict(di)))


if __name__ == "__main__":
    do_list_displays()
