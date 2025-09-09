# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
PsychoPy-based script to produce time calibration session
with embedded video QR-codes and audiocodes integrated
with `MRI`/`BIRCH`/`Magewell USB capture` devices.

API to parse `(*.mkv)` video files recorded by `reprostim-videocapture`
utility and extract embedded video media info, QR-codes and audiocodes into
JSONL format.
"""
import types
from dataclasses import dataclass
from time import sleep, time

t0 = time()

import importlib.util
import logging
import os
import shutil
import signal
from datetime import datetime
from enum import Enum

from ..__about__ import __version__

# setup logging
logger = logging.getLogger(__name__)
logger.info("reprostim timesync-stimuli script started")


#######################################################
# Constants

MAX_TR_TIMEOUT: float = 4.0


class Mode(str, Enum):
    """Enum for the mode of the script operation."""

    EVENT = "event"
    """Listen for keyboard events or MRI pulse and generate QR/audio codes."""
    INTERVAL = "interval"
    """Produce QR/audio codes at regular intervals."""
    # Just play a beep
    BEEP = "beep"
    """Play a beep sound for audio test purposes."""
    DEVICES = "devices"
    """List available audio devices to the console output."""


#######################################################
# Classes


@dataclass
class SeriesData:
    """Class to hold series data for trigger events."""

    num: int
    """Series number."""
    tr_count: int = 0
    """Trigger events count in the series."""
    tr_last_time: float = None
    """Last trigger event time."""
    tr_timeout: float = MAX_TR_TIMEOUT
    """Trigger event max interval/timeout in seconds."""


#######################################################
# Functions


def get_output_file_name(
    prefix: str, start_ts: datetime, end_ts: datetime = None
) -> str:
    """
    Generates an output file name based on the given prefix and timestamps.

    This function creates a file name by formatting the provided start and
    optional end timestamps into a string and appending them to the provided
    prefix. The timestamps are converted to strings using the `get_ts_str`
    function.

    :param prefix: The prefix to use for the file name.
    :type prefix: str

    :param start_ts: The start timestamp to be included in the file name.
    :type start_ts: datetime

    :param end_ts: The optional end timestamp to be included in the file name.
    :type end_ts: datetime, optional

    :return: The generated file name.
    :rtype: str
    """
    start_str: str = get_ts_str(start_ts)
    end_str: str = get_ts_str(end_ts) if end_ts else ""
    return f"{prefix}{start_str}--{end_str}.log"


def get_ts_str(ts: datetime) -> str:
    """Get a formatted string representation of a timestamp.

    This function formats the provided timestamp into a string using
    the specified format (`%Y.%m.%d-%H.%M.%S.%f`). The format includes
    year, month, day, hour, minute, second, and microsecond.

    :param ts: The timestamp to be formatted.
    :type ts: datetime

    :return: The formatted string representation of the timestamp.
    :rtype: str
    """
    ts_format = "%Y.%m.%d-%H.%M.%S.%f"
    return f"{ts.strftime(ts_format)[:-3]}"


def safe_remove(file_name: str):
    """Safely remove a file if it exists.

    This function checks if the specified file exists and is a valid file.
    If it is, it attempts to remove the file. If the removal fails,
    it logs an error message.

    :param file_name: The name of the file to be removed.
    :type file_name: str
    """
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
    """Store the audio code data in to the standalone `*.wav` file.

    :param audio_file: The path to the audio file to be copied.
    :type audio_file: str

    :param audio_data: The audio data used in audio code.
    :type audio_data: int

    :param logfn: The current log file name.
    :type logfn: str
    """
    # if audio_file exits, copy it to {logfn}audiocode_{audio_data}.wav
    if os.path.isfile(audio_file):
        sfile = f"{os.path.splitext(logfn)[0]}audiocode_{audio_data}.wav"
        shutil.copy(audio_file, sfile)


#######################################################
# Main script code


def do_init(logfn: str) -> bool:
    """
    Initializes a log file.

    :param logfn: The path to the log file to be checked.
    :type logfn: str

    :return: `True` if the log file does not exist and can be
              initialized, `False` otherwise.
    :rtype: bool
    """
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
    qr_duration: float,
    qr_async: bool,
    audio_codec: str,
    mute: bool,
    ntrials: int,
    duration: float,
    interval: float,
    keep_audiocode: bool,
    out_func=print,
) -> int:
    """Main function to run the `timesync-stimuli` PsychoPy-based script.

    This function initializes the PsychoPy environment, sets up the window,
    and handles the main loop for displaying QR codes and audio codes.
    It also handles keyboard events and manages the series of trigger events.
    The function takes various parameters to configure the behavior of the script.

    :param mode: The mode of operation (e.g., EVENT, INTERVAL, BEEP, DEVICES).
    :type mode: Mode

    :param logfn: The name of the log file to write to.
    :type logfn: str

    :param is_fullscreen: Whether to run the window in fullscreen mode.
    :type is_fullscreen: bool

    :param win_size: The size of the window (width, height) in pixels.
    :type win_size: tuple[int, int]

    :param display: The display number to use.
    :type display: int

    :param qr_scale: The scale factor for the QR code size.
    :type qr_scale: float

    :param qr_duration: The duration of the QR code display in seconds.
    :type qr_duration: float

    :param qr_async: Whether to display the QR code asynchronously.
    :type qr_async: bool

    :param audio_codec: The audio codec to use for the audio code.
    :type audio_codec: str

    :param mute: Whether to mute the audio output.
    :type mute: bool

    :param ntrials: The number of trials to run.
    :type ntrials: int

    :param duration: The duration of the experiment in seconds.
    :type duration: float

    :param interval: The interval between trials in seconds.
    :type interval: float

    :param keep_audiocode: Whether to keep the audio code file after use.
    :type keep_audiocode: bool

    :param out_func: The function to use for output (default is `print`).
    :type out_func: callable

    :return: 0 on success, -1 on error.
    :rtype: int
    """
    logger.info("main script started")

    if not importlib.util.find_spec("psychopy"):
        logger.error(
            "Module 'psychopy' not found, re-install environment with [all] extras"
        )
        return -1

    # late psychopy init
    # setup psychopy logs
    from psychopy import logging as pl

    from reprostim.qr.psychopy import (
        EventType,
        QrCode,
        QrStim,
        get_iso_time,
        get_times,
        to_json,
    )

    # psychopy logging doesn't support filtering by message content,
    # so this is a patch to filter out flooding messages like "No keypress"
    _pl_log_method = pl.root.log

    def pl_filtered_log(self, message_, level, t=None, obj=None):
        if "No keypress (maxWait exceeded)" in str(message_):
            return
        _pl_log_method(message_, level, t, obj)

    pl.root.log = types.MethodType(pl_filtered_log, pl.root)

    # pl.console.setLevel(pl.NOTSET)
    pl.console.setLevel(pl.DEBUG)

    def log(f, rec):
        """Log a QR record to a file.

        This function takes a file handle and a record dictionary,
        converts the record to a JSON string, and writes it to the file.

        :param f: The file handle to write the log to.
        :type f: file object

        :param rec: The record dictionary to be logged.
        :type rec: dict
        """
        s = to_json(rec).rstrip()
        f.write(s + os.linesep)
        logger.debug(f"LOG {s}")

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
    w_keys: list[str] = []

    def check_keys(max_wait: float = 0) -> list[str]:
        nonlocal w_keys
        keys: list[str]

        # use cached keys if any
        if w_keys:
            keys = w_keys
            w_keys = []
            return keys

        if max_wait > 0:
            keys = event.waitKeys(maxWait=max_wait)
        else:
            keys = event.getKeys()
        logger.debug(f"keys={keys}")
        return keys if keys else []

    def on_signal(signum, frame):
        logger.info(f"Received system signal: {signum}")
        if signum in [2, 15]:
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
            QrCode(
                event=EventType.SERIES_START,
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
                QrCode(
                    event=EventType.SERIES_END,
                    mode=mode,
                    logfn=logfn,
                    series_num=sd.num,
                    trigger_count=sd.tr_count,
                ),
            )
            out_func(f"Series [{sd.num}] ended, trigger count: {sd.tr_count}")
        return None

    def wait_or_keys(
        timeout: float = 0,
        async_: bool = False,
        break_keys=None,
    ) -> list[str]:
        if async_:
            # use manual wait loop
            start_time = core.getTime()

            # wait loop
            while core.getTime() - start_time < timeout:
                keys = event.getKeys(keyList=break_keys)
                if keys:
                    return keys
                core.wait(0.001)  # reduce CPU usage and pass control to other threads
        else:
            core.wait(timeout)

        return []

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

    if win.monitor:
        logger.info(f"display [{display}] info:")
        fr = win.getActualFrameRate()
        logger.info(
            f"    {win.size[0]}x{win.size[1]} px, " f"    {round(fr, 2)} Hz"
            if fr
            else "    N/A Hz"
        )

    # log script started event
    log(
        f,
        QrCode(
            event=EventType.SESSION_START,
            mode=mode,
            logfn=logfn,
            start_time=t0,
            start_time_formatted=get_iso_time(t0),
        ),
    )

    # test audio first on startup
    if not mute:
        logger.info("check audio code and output...")
        test_duration: float = 0.05
        # decrease volume
        test_volume: float = 0.05
        a_file, a_info = save_audiocode(
            code_uint16=0, codec=AudioCodec.NFE, code_duration=test_duration
        )
        logger.info(f"    {a_info}")
        play_audio(a_file, volume=test_volume, async_=True)
        wait_or_keys(test_duration, async_=False)
        safe_remove(a_file)

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
                code_uint16=audio_data, codec=audio_codec, code_duration=qr_duration
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
        rec = QrCode(
            event=EventType.MRI_TRIGGER_RECEIVED, mode=mode, logfn=logfn, acqNum=acqNum
        )

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
        qr = QrStim(win, rec, pos=(0, 0))
        qr.size = qr.size * qr_scale  # TODO: move to QrConfig
        qr.draw()
        win.flip()
        tflip, tflip_str = get_times()
        rec["time_flip"] = tflip
        rec["time_flip_formatted"] = tflip_str
        w_keys = wait_or_keys(qr_duration, qr_async, ["5", "num_5", "escape", "q"])
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
