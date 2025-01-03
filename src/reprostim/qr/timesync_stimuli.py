# SPDX-FileCopyrightText: 2024-present ReproNim <info@repronim.org>
#
# SPDX-License-Identifier: MIT

from time import sleep, time

t0 = time()

import importlib.util
import json
import logging
import os
import shutil
from datetime import datetime
from enum import Enum

import qrcode

# setup logging
logger = logging.getLogger(__name__)
logger.info("reprostim timesync-stimuli script started")


#######################################################
# Constants


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


def mkrec(mode, logfn, interval, **kwargs):
    t, tstr = get_times()
    kwargs.update(
        {
            "logfn": logfn,
            "time": t,
            "time_formatted": tstr,
            "mode": mode,
        }
    )
    if mode == "interval":
        kwargs["interval"] = interval
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
    display: int,
    qr_scale: float,
    audio_codec: str,
    mute: bool,
    ntrials: int,
    duration: float,
    interval: float,
    keep_audiocode: bool,
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

    def check_keys(max_wait: float = 0) -> list[str]:
        keys: list[str]
        if max_wait > 0:
            keys = event.waitKeys(maxWait=max_wait)
        else:
            keys = event.getKeys()
        logger.debug(f"keys={keys}")
        return keys if keys else []

    if mode == Mode.BEEP:
        for _ in range(ntrials):
            beep(interval * 0.5, async_=True)
            sleep(interval)
        return 0

    if mode == Mode.DEVICES:
        list_audio_devices()
        return 0

    audio_data: int = 0
    audio_file: str = None
    audio_info: AudioCodeInfo = None
    f = open(logfn, "w")

    win = visual.Window(fullscr=True, screen=display)
    win.mouseVisible = False  # hides the mouse pointer

    log(
        f,
        mkrec(
            mode,
            logfn,
            interval,
            event="started",
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

    logger.debug(f"warming time: {(t_start-t0):.6f} sec")
    logger.info(f"starting loop with {ntrials} trials...")

    for acqNum in range(ntrials):
        logger.debug(f"trial {acqNum}")

        rec = mkrec(mode, logfn, interval, event="trigger", acqNum=acqNum)

        if mode == Mode.EVENT:
            print("Waiting for an event")
            keys = check_keys(120)  # keyList=['5'])
        elif mode == Mode.INTERVAL:
            # keys = kb.getKeys(waitRelease=False)
            keys = check_keys()
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

            target_time = t_start + acqNum * interval
            to_wait = target_time - time()
            # sleep some part of it if long enough
            if to_wait >= 0.2:
                sleep(to_wait * 0.7)
            # busy loop without sleep to not miss it
            while time() < target_time:
                sleep(0)  # pass CPU to other threads
        else:
            raise ValueError(mode)

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
        if "q" in keys or "escape" in keys:
            break

    f.close()

    if keep_audiocode and audio_file:
        store_audiocode(audio_file, audio_data, logfn)
    # cleanup temporary audio code file if any
    safe_remove(audio_file)
    logger.info("main script finished")
    return 0
