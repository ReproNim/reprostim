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
from itertools import chain
from typing import Generator

# initialize the logger
logger = logging.getLogger(__name__)
# logging.getLogger().setLevel(logging.DEBUG)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logger.debug(f"name={__name__}")


# Platform constants
class DmPlatform(str, Enum):
    LINUX = "linux"
    XOS = "xos"
    # WINDOWS = "win64"


# Service provider constants
class DmProvider(str, Enum):
    """Enum to represent the display monitoring provider/engine
    depending on used OS environment."""

    PLATFORM = "platform"  # Default OS specific providers
    PYGAME = "pygame"  # Cross-platform
    PYGLET = "pyglet"  # Cross-platform
    PYUDEV = "pyudev"  # Used in Linux
    QUARTZ = "quartz"  # Used in macOS
    RANDR = "randr"  # Used in Linux


# import necessary provider implementation in runtime based on OS type
if sys.platform.startswith("linux"):
    import pyudev
    from Xlib import display
    from Xlib.ext import randr

    _PLATFORM = DmPlatform.LINUX
elif sys.platform == "darwin":
    import Quartz

    _PLATFORM = DmPlatform.XOS
else:
    logger.error(f"Unsupported OS: {sys.platform}")
    raise NotImplementedError(f"Unsupported OS: {sys.platform}")

logger.debug(f"Use '{_PLATFORM}' platform.")

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


# pygame implementation
def _enum_displays_pygame() -> Generator[DisplayInfo, None, None]:
    import pygame

    # Initialize Pygame
    pygame.display.init()

    # Get the number of available screens
    disp_count = pygame.display.get_num_displays()
    logger.debug(f"Number of displays connected: {disp_count}")

    # default display info
    def_disp_info = pygame.display.Info()
    def_w = def_disp_info.current_w
    def_h = def_disp_info.current_h
    logger.debug(f"Default display resolution: {def_w}x{def_h}")

    # Loop through each screen and list available modes
    for i in range(disp_count):
        logger.debug(f"Display {i}:")
        di: DisplayInfo = DisplayInfo()
        di.provider = DmProvider.PYGAME
        di.id = i
        di.name = f"display-{i}"

        # logger.debug(f"  Active: {pygame.display.get_active()}")

        disp_w, disp_h = pygame.display.get_desktop_sizes()[i]
        logger.debug(f"  Resolution: {disp_w}x{disp_h}")
        di.is_connected = True
        di.is_active = True
        di.width = disp_w
        di.height = disp_h

        if disp_w == def_w and disp_h == def_h:
            di.is_main = True

        # pygame.display.set_mode((desktop_size[0], desktop_size[1]),
        # pygame.FULLSCREEN, display=i)
        # inf = pygame.display.Info()

        # Get available resolutions for the current display
        # modes = pygame.display.list_modes(display=i)
        # logger.debug(f"Available resolutions on Display {i}:")
        # for mode in modes:
        #    logger.debug(f"{mode[0]}x{mode[1]}")
        yield di

    pygame.display.quit()


# pyglet implementation
def _enum_displays_pyglet() -> Generator[DisplayInfo, None, None]:
    # handle both pyglet versions
    import pyglet

    if hasattr(pyglet, "display"):
        from pyglet.display import get_display, Display
    elif hasattr(pyglet, "canvas"):
        from pyglet.canvas import get_display, Display

    # trace version info
    if hasattr(pyglet, "c"):
        logger.debug(f"pyglet version: {pyglet.c}")


    display = get_display()

    primary_screen = display.get_default_screen()

    # Get all screens connected to the display
    screens = display.get_screens()

    # Enumerate and print screen details
    for i, scr in enumerate(screens):
        # Note: scr has private _cg_display_id property
        # with quartz display ID as well in xos.

        di: DisplayInfo = DisplayInfo()
        di.provider = DmProvider.PYGLET
        di.id = i
        di.name = f"screen-{i}"
        di.is_connected = True
        di.is_active = True

        logger.debug(f"Screen {i}:")
        if hasattr(scr, "get_nsscreen"):
            logger.debug(f"  NSScreen: {scr.get_nsscreen()}")
        if (
            scr.display == primary_screen.display
            and scr.width == primary_screen.width
            and scr.height == primary_screen.height
            and scr.x == primary_screen.x
            and scr.y == primary_screen.y
        ):
            logger.debug("  primary")
            di.is_main = True

        logger.debug(f"  pos  : [{scr.x}, {scr.y}]")
        logger.debug(f"  size : {scr.width}x{scr.height}")
        di.width = scr.width
        di.height = scr.height

        #scr._xinerama = False
        modes = scr.get_modes()
        logger.debug(f"  modes: {modes}")
        # find current mode if any
        for mode in modes:
            if mode.width == scr.width and mode.height == scr.height:
                logger.debug(f"  current mode : {mode}")
                di.refresh_rate = mode.rate
                di.bits_per_pixel = mode.depth

                # fix issue in pyglet/xlib, convert dotclock to refresh rate
                if type(mode).__name__ == "XlibScreenMode":
                    logger.debug("fix rate")
                    if mode.info.htotal != 0 and mode.info.vtotal != 0 :
                        di.refresh_rate = (mode.info.dotclock*1000.0) / (mode.info.htotal * mode.info.vtotal)
                break

        yield di



# pyudev implementation
def _enum_displays_pyudev() -> Generator[DisplayInfo, None, None]:
    ctx = pyudev.Context()

    # Look for devices under the 'drm' subsystem
    for d in ctx.list_devices(subsystem="drm"):
        if "DEVNAME" in d and "ID_PATH" in d:
            logger.debug("Display: ")
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
            di.id = d.get("ID_PATH")
            di.name = d.device_node
            # strip prefix to get the name optionally
            if di.name.startswith("/dev/dri/"):
                di.name = di.name[9:]
            di.is_connected = True

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
            out_info = randr.get_output_info(root, output, scr_res.config_timestamp)
            scr_name = out_info.name  # .decode("utf-8")
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

            crtc_info = randr.get_crtc_info(
                root, out_info.crtc, scr_res.config_timestamp
            )

            # Get max screen width and height
            scr_max_width = crtc_info.width
            scr_max_height = crtc_info.height
            logger.debug(f"  max resolution: {scr_max_width}x{scr_max_height}")

            # Find active mode refresh rate
            for mode in scr_res.modes:
                if mode.id == crtc_info.mode:
                    refresh_rate = round(
                        mode.dot_clock / (mode.h_total * mode.v_total), 2
                    )
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

    # TODO: find display name,
    #    see also NSScreen.screens @NSScreenNumber to match
    #    with display_id (CGDirectDisplayID)
    #    [https://stackoverflow.com/questions/1236498/how-to-
    #    get-the-display-name-with-the-display-id-in-mac-os-x]
    #    https://github.com/johnjohndoe/DisplayInfo
    #
    # from serial.tools.list_ports_osx import (GetIOServicesByType,
    #                                          IORegistryEntryGetName,
    #                                          get_string_property,
    #                                          get_int_property)
    #
    # services = GetIOServicesByType("IODisplayConnect")
    # logger.debug(f"services={services}")
    # for dev_type in services:
    #    logger.debug(f"dev_type={dev_type}")
    #    den_ename = IORegistryEntryGetName(dev_type)
    #    logger.debug(f"den_ename={den_ename}")
    #    name = get_string_property(dev_type, "AppleDisplay")
    #    logger.debug(f"name={name}")

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


def enum_displays(
    provider: DmProvider = DmProvider.PLATFORM,
) -> Generator[DisplayInfo, None, None]:
    a = []
    if provider == DmProvider.PLATFORM:
        if _PLATFORM == DmPlatform.LINUX:
            a.append(_enum_displays_pyudev())
            a.append(_enum_displays_randr())
        elif _PLATFORM == DmPlatform.XOS:
            a.append(_enum_displays_quartz())
        else:
            raise NotImplementedError(f"Unsupported platform: {_PLATFORM}")
        # add cross-platform providers as well
        # a.append(_enum_displays_pygame())
        a.append(_enum_displays_pyglet())
    elif provider == DmProvider.PYUDEV:
        a.append(_enum_displays_pyudev())
    elif provider == DmProvider.QUARTZ:
        a.append(_enum_displays_quartz())
    elif provider == DmProvider.RANDR:
        a.append(_enum_displays_randr())
    elif provider == DmProvider.PYGAME:
        a.append(_enum_displays_pygame())
    elif provider == DmProvider.PYGLET:
        a.append(_enum_displays_pyglet())
    else:
        raise NotImplementedError(f"Unsupported provider: {provider}")
    return chain(*a)


def do_list_displays(
    provider: DmProvider = DmProvider.PLATFORM, fmt: str = "jsonl", out_func=print
):
    logger.debug("do_list_displays()")

    last_provider: DmProvider = None
    fmt = fmt.lower()  # make it case-insensitive

    for di in enum_displays(DmProvider(provider)):
        if fmt == "jsonl":
            out_func(json.dumps(asdict(di)))
        elif fmt == "text":
            if last_provider != di.provider:
                last_provider = di.provider
                out_func(f"[{di.provider}]")

            mode: str = (
                f" {di.width}x{di.height}" if di.is_connected and di.width > 0 else ""
            )
            rate: str = (
                f" {round(di.refresh_rate, 2)}Hz"
                if di.is_connected and di.refresh_rate > 0
                else ""
            )
            out_func(
                f"  {di.name} [{di.id}] :{mode}{rate}"
                f"{' connected' if di.is_connected else ' disconnected'}"
                f"{' active' if di.is_active else ''}"
                f"{' primary' if di.is_main else ''}"
            )
        else:
            raise NotImplementedError(f"Unknown format: {format}")


if __name__ == "__main__":
    do_list_displays(DmProvider.PLATFORM, "text")
    # do_list_displays(DmProvider.PYGAME, "text")
    # do_list_displays(DmProvider.PYGLET, "text")
