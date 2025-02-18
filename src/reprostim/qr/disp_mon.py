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
from itertools import chain

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
    RANDR  = "randr"   # Used in Linux


# import necessary provider implementation in runtime based on OS type
if sys.platform.startswith("linux"):
    from Xlib import display
    from Xlib.ext import randr
    import pyudev

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
    id: str = None
    name: str = None
    width: int = 0
    height: int = 0
    refresh_rate: float = 0.0
    bits_per_pixel: int = 0
    is_connected: bool = False
    is_active: bool = False
    is_main: bool = False
    is_sleeping: bool = False
    provider: DmProvider = None


# pyudev implementation
def _enum_displays_pyudev() -> Generator[DisplayInfo, None, None]:
    ctx = pyudev.Context()

    # Look for devices under the 'drm' subsystem
    for d in ctx.list_devices(subsystem='drm'):
        if 'DEVNAME' in d and 'ID_PATH' in d:
            logger.debug(f"Display: ")
            logger.debug(f"  device_node = {d.device_node}")
            logger.debug(f"  ID_PATH     = {d.get('ID_PATH')}")
            for k in d.properties.keys():
                logger.debug(f"  {k} = {d.properties[k]}")
            # logger.debug(f"  props       = {d.properties}")
            di: DisplayInfo = DisplayInfo()
            di.provider = DmProvider.PYUDEV
            # Note: ID_PATH may contain PCI address
            # like pci-0000:01:00.0 or similar,
            # it can be mapped to name by looking at
            #    ls -l /sys/class/drm/
            di.id = d.get('ID_PATH')
            di.name = d.device_node

            yield di


# randr implementation
def _enum_displays_randr() -> Generator[DisplayInfo, None, None]:
    # Open display connection,
    # TODO: use $DISPLAY data like param e.g. ":0"?
    d = display.Display()
    try:
        root = d.screen().root

        # Get screen resources
        scr_res = randr.get_screen_resources(root)

        # Get the current mode of the primary output
        outputs = scr_res.outputs
        if not outputs:
            logger.debug("No connected outputs found")
            return

        # Iterate over all outputs to find the active one
        for output in outputs:
            di: DisplayInfo = DisplayInfo()
            di.provider = DmProvider.RANDR
            out_info = randr.get_output_info(root, output,
                                             scr_res.config_timestamp)
            scr_name = out_info.name #.decode("utf-8")
            logger.debug(f"Screen name: {scr_name}")
            di.id = scr_name
            di.name = scr_name

            # TODO: check if primary or secondary, e.g vi
            #  xrandr_get_output_primary() or
            # if ??? :
            #     logger.debug("  primary")
            #     di.is_main = True
            # else:
            #     logger.debug("  secondary")
            #     di.is_main = False

            if out_info.connection == 0:
                logger.debug("  connected")
                di.is_connected = True
            else:
                logger.debug("  disconnected")
                di.is_connected = False

            if out_info.crtc == 0:
                logger.debug("  not active")
                di.is_active = False
                yield di
                continue  # Skip outputs that are not active
            else:
                logger.debug("  active")
                di.is_active = True

            crtc_info = randr.get_crtc_info(root, out_info.crtc,
                                            scr_res.config_timestamp)

            # Get max screen width and height
            scr_max_width = crtc_info.width
            scr_max_height = crtc_info.height
            logger.debug(f"  max resolution: {scr_max_width}x{scr_max_height}")

            # Find active mode refresh rate
            for mode in scr_res.modes:
                if mode.id == crtc_info.mode:
                    refresh_rate = round((mode.dot_clock * 1000) / (mode.h_total * mode.v_total), 2)
                    di.refresh_rate = refresh_rate
                    logger.debug(f"  refresh rate: {refresh_rate} Hz")
                    di.width = mode.width
                    di.height = mode.height
                    logger.debug(f"  resolution: {mode.width}x{mode.height}")
                    break

            yield di
    finally:
        d.close()


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
        di.provider = DmProvider.QUARTZ
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
        return chain(_enum_displays_pyudev(),
                        _enum_displays_randr())
    else:
        raise NotImplementedError(f"Unsupported OS: {sys.platform}")


def do_list_displays():
    logger.debug("do_list_displays()")
    for di in enum_displays():
        print(json.dumps(asdict(di)))


if __name__ == "__main__":
    do_list_displays()
