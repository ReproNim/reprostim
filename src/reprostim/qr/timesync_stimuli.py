# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from time import sleep, time

t0 = time()

import importlib.util
import json
import logging
import os
import shutil
import signal
from datetime import datetime
from enum import Enum

import qrcode

from ..__about__ import __version__

# setup logging
logger = logging.getLogger(__name__)
logger.info("reprostim timesync-stimuli script started")


#######################################################
# Constants

MAX_TR_TIMEOUT: float = 4.0


# Enum for the log event names
class EventName(str, Enum):
    STARTED = "started"
    SERIES_BEGIN = "series_begin"
    SERIES_END = "series_end"
    TRIGGER = "trigger"


# Enum for the mode of the script operation
class Mode(str, Enum):
    # Listen for keyboard events to show codes
    EVENT = "event"
    # Show codes at regular intervals
    INTERVAL = "interval"
    # Just play a beep
    BEEP = "beep"
    # List audio/video devices
    DEVICES = "devices"


#######################################################
# Classes


@dataclass
class SeriesData:
    num: int  # series number
    tr_count: int = 0  # trigger events count in the series
    tr_last_time: float = None  # last trigger event time()
    tr_timeout: float = MAX_TR_TIMEOUT  # trigger event max timeout


#######################################################
# Functions


def get_iso_time(t):
    return datetime.fromtimestamp(t).astimezone().isoformat()


def get_output_file_name(
    prefix: str, start_ts: datetime, end_ts: datetime = None
) -> str:
    start_str: str = get_ts_str(start_ts)
    end_str: str = get_ts_str(end_ts) if end_ts else ""
    return f"{prefix}{start_str}--{end_str}.log"


def get_times():
    t = time()
    return t, get_iso_time(t)


def get_ts_str(ts: datetime) -> str:
    ts_format = "%Y.%m.%d-%H.%M.%S.%f"
    return f"{ts.strftime(ts_format)[:-3]}"


def log(f, rec):
    s = json.dumps(rec).rstrip()
    f.write(s + os.linesep)
    logger.debug(f"LOG {s}")


def mkrec(**kwargs):
    t, tstr = get_times()
    kwargs.update(
        {
            "time": t,
            "time_formatted": tstr,
        }
    )
    return kwargs


def safe_remove(file_name: str):
    if file_name:
        if os.path.isfile(file_name):  # Check if it's a file
            try:
                os.remove(file_name)
                logger.debug(f"File {file_name} deleted successfully.")
            except Exception as e:
                logger.error(f"Failed delete file {file_name}: {e}")
        else:
            logger.warning(f"File {file_name} does not exist or is not a valid file.")


def store_audiocode(audio_file: str, audio_data: int, logfn: str):
    # if audio_file exits, copy it to {logfn}audiocode_{audio_data}.wav
    if os.path.isfile(audio_file):
        sfile = f"{os.path.splitext(logfn)[0]}audiocode_{audio_data}.wav"
        shutil.copy(audio_file, sfile)


#######################################################
# Main script code


def do_init(logfn: str) -> bool:
    if os.path.exists(logfn):
        logger.error(f"Log file {logfn} already exists")
        return False
    return True


def do_main(
    mode: Mode,
    logfn: str,
    is_fullscreen: bool,
    win_size: tuple[int, int],
    display: int,
    qr_scale: float,
    audio_codec: str,
    mute: bool,
    ntrials: int,
    duration: float,
    interval: float,
    keep_audiocode: bool,
    out_func=print,
) -> int:
    logger.info("main script started")

    if not importlib.util.find_spec("psychopy"):
        logger.error(
            "Module 'psychopy' not found, re-install environment with [all] extras"
        )
        return -1

    # late psychopy init
    # setup psychopy logs
    from psychopy import logging as pl

    # pl.console.setLevel(pl.NOTSET)
    pl.console.setLevel(pl.DEBUG)

    from psychopy import core, event, visual

    # from psychopy.hardware import keyboard
    # late audio init
    from ..audio.audiocodes import (
        AudioCodec,
        AudioCodeInfo,
        beep,
        list_audio_devices,
        play_audio,
        save_audiocode,
    )

    sys_shutdown: bool = False

    def check_keys(max_wait: float = 0) -> list[str]:
        keys: list[str]
        if max_wait > 0:
            keys = event.waitKeys(maxWait=max_wait)
        else:
            keys = event.getKeys()
        logger.debug(f"keys={keys}")
        return keys if keys else []

    def on_signal(signum, frame):
        logger.info(f"Received system signal: {signum}")
        if signum in [2, 15] :
            nonlocal sys_shutdown
            logger.debug("setting sys_shutdown=True")
            sys_shutdown = True

    def series_begin(series_num: int) -> SeriesData:
        sd = SeriesData(num=series_num, tr_count=0, tr_timeout=MAX_TR_TIMEOUT)
        logger.debug(f"series begin: {sd.num}")
        # log series begin event
        nonlocal f
        log(
            f,
            mkrec(
                event=EventName.SERIES_BEGIN,
                mode=mode,
                logfn=logfn,
                series_num=sd.num,
            ),
        )
        out_func(f"Series [{sd.num}] started")
        return sd

    def series_end(sd: SeriesData) -> SeriesData:
        if sd:
            logger.debug(f"series end: {sd.num}")
            # log series end event
            nonlocal f
            log(
                f,
                mkrec(
                    event=EventName.SERIES_END,
                    mode=mode,
                    logfn=logfn,
                    series_num=sd.num,
                    trigger_count=sd.tr_count,
                ),
            )
            out_func(f"Series [{sd.num}] ended, trigger count: {sd.tr_count}")
        return None

    if mode == Mode.BEEP:
        for _ in range(ntrials):
            beep(interval * 0.5, async_=True)
            sleep(interval)
        return 0

    if mode == Mode.DEVICES:
        list_audio_devices()
        return 0

    # register signal hook
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)


    audio_data: int = 0
    audio_file: str = None
    audio_info: AudioCodeInfo = None
    f = open(logfn, "w")

    win = visual.Window(
        fullscr=is_fullscreen,
        title=f"ReproStim timesync-stimuli v{__version__}",
        name="timesync-stimuli",
        size=win_size,
        screen=display,
    )
    logger.debug(f"win.winHandle class: {type(win.winHandle).__name__}")
    win.winHandle.on_activate = lambda: out_func("Window activated")
    win.winHandle.on_activate()
    win.winHandle.on_deactivate = lambda: out_func("Window deactivated")
    # win.winHandle.set_caption(win.title)
    win.mouseVisible = False  # hides the mouse pointer
    # win.winHandle.activate()

    # log script started event
    log(
        f,
        mkrec(
            event=EventName.STARTED,
            mode=mode,
            logfn=logfn,
            start_time=t0,
            start_time_formatted=get_iso_time(t0),
        ),
    )

    message = visual.TextStim(
        win,
        text="""Waiting for scanner trigger.\nInstructions
            for Participant...""",
    )
    message.draw()

    fixation = visual.TextStim(win, text="+")
    visual.TextStim(win, text="", pos=(0, -0.7), height=0.05)

    win.flip()

    fixation.draw()  # Change properties of existing stim
    win.flip()

    # spd = 0.500  # Stimulus Presentation Duration
    # soa = 6.000  # Stimulus Onset Asynchrony
    # iwt = 5  # Initial Wait Time between scanner trigger and first stimulus

    # stim_images = []
    # stim_names = []
    # keys = []  # None received/expected

    # kb = keyboard.Keyboard()

    t_start = time()
    t_end = t_start + duration if duration > 0 else None

    logger.debug(f"warming time: {(t_start-t0):.6f} sec")
    logger.debug(f"starting loop with {ntrials} trials...")

    terminate: bool = False

    series_num: int = 0
    cur_series: SeriesData = None

    for acqNum in range(ntrials):
        # check the duration time limit
        if t_end and time() > t_end:
            out_func("Time is up!")
            terminate = True

        # exit processing loop if requested
        if terminate:
            break

        logger.debug(f"trial {acqNum}")

        # prepare audio code file if any
        if not mute:
            if keep_audiocode and audio_file:
                store_audiocode(audio_file, audio_data, logfn)
            safe_remove(audio_file)
            audio_data = acqNum
            audio_file, audio_info_ = save_audiocode(
                code_uint16=audio_data, codec=audio_codec
            )
            audio_info = audio_info_
            logger.debug(f"  {audio_info}")

        if mode == Mode.EVENT:
            out_func("Waiting for an event...")
            while True:
                if sys_shutdown:
                    break

                # check the duration time limit
                if t_end and time() > t_end:
                    out_func("Time is up!")
                    terminate = True
                    break
                keys = check_keys(0.2)
                # only break if 5 or exit keys are pressed
                if (
                    keys
                    and len(keys) > 0
                    and (
                        "q" in keys
                        or "escape" in keys
                        or "5" in keys
                        or "num_5" in keys
                    )
                ):
                    break
                # additional check the series if any expired
                # inside the trigger pulse waiting loop
                if (
                    cur_series
                    and cur_series.tr_count > 0
                    and (time() - cur_series.tr_last_time) > cur_series.tr_timeout
                ):
                    logger.debug("series expired")
                    cur_series = series_end(cur_series)

            # break external loop/terminate
            if terminate:
                break

            if sys_shutdown:
                out_func("Shutdown timesync-stimuli...")
                break

            if cur_series and cur_series.tr_count > 0:
                # calculate time delta from last impulse if any
                dt: float = time() - cur_series.tr_last_time

                if dt > cur_series.tr_timeout:
                    logger.debug(f"timed out after {dt} sec, renew series")
                    cur_series = series_end(cur_series)
                else:
                    # after receiving two first consecutive triggers
                    # pulses -- take the temporal distance between
                    # them +50% as the next value of tr_timeout
                    if cur_series.tr_count == 1:
                        cur_series.tr_timeout = dt * 1.5
                        logger.debug(f"update tr_timeout: {cur_series.tr_timeout}")

        elif mode == Mode.INTERVAL:
            # keys = kb.getKeys(waitRelease=False)
            keys = check_keys()

            target_time = t_start + acqNum * interval
            to_wait = target_time - time()
            # sleep some part of it if long enough
            if to_wait >= 0.2:
                sleep(to_wait * 0.7)
            # busy loop without sleep to not miss it
            while time() < target_time:
                sleep(0)  # pass CPU to other threads
                if sys_shutdown:
                    break
            # 2nd break
            if sys_shutdown:
                out_func("Shutdown timesync-stimuli...")
                break
        else:
            raise ValueError(mode)

        # start series if not started
        if not cur_series:
            cur_series = series_begin(series_num)
            series_num += 1

        # trigger record,
        rec = mkrec(event=EventName.TRIGGER, mode=mode, logfn=logfn, acqNum=acqNum)

        if cur_series:
            rec["series_num"] = cur_series.num

        if mode == Mode.INTERVAL:
            rec["interval"] = interval

        if not mute:
            play_audio(audio_file, async_=True)
            audio_time, audio_time_str = get_times()
            rec["a_time"] = audio_time
            rec["a_time_str"] = audio_time_str
            rec["a_data"] = audio_data
            rec["a_codec"] = audio_codec
            rec["a_f0"] = audio_info.f0
            rec["a_f1"] = audio_info.f1
            rec["a_pre_delay"] = audio_info.pre_delay
            rec["a_post_delay"] = audio_info.post_delay
            rec["a_duration"] = audio_info.duration
            if audio_codec == AudioCodec.NFE:
                rec["a_freq"] = audio_info.nfe_freq
                rec["a_df"] = audio_info.nfe_df

            # NOTE: should we add codec info to the log?
            # like f0, f1, sampleRate, bit_duration, duration, etc

        rec["keys"] = keys
        tkeys, tkeys_str = get_times()
        rec["keys_time"] = tkeys
        rec["keys_time_str"] = tkeys_str
        qr = visual.ImageStim(win, qrcode.make(json.dumps(rec)), pos=(0, 0))
        qr.size = qr.size * qr_scale
        qr.draw()
        win.flip()
        tflip, tflip_str = get_times()
        rec["time_flip"] = tflip
        rec["time_flip_formatted"] = tflip_str
        core.wait(0.5)
        fixation.draw()
        win.flip()
        toff, toff_str = get_times()
        rec["prior_time_off"] = toff
        rec["prior_time_off_str"] = toff_str
        log(f, rec)
        out_func(
            f"Trigger pulse: acq={acqNum}, "
            f"series={cur_series.num if cur_series else 'N/A'}, "
            f"keys={keys}"
        )
        # update trigger event series data
        if cur_series:
            cur_series.tr_count = cur_series.tr_count + 1
            cur_series.tr_last_time = tkeys
        if "q" in keys or "escape" in keys:
            break

    cur_series = series_end(cur_series)

    f.close()

    if keep_audiocode and audio_file:
        store_audiocode(audio_file, audio_data, logfn)
    # cleanup temporary audio code file if any
    safe_remove(audio_file)
    logger.info("main script finished")
    return 0
