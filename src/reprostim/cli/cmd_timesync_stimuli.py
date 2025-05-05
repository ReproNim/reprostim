# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os
from datetime import datetime

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(help="PsychoPy reprostim timesync-stimuli script.")
@click.option(
    "-m",
    "--mode",
    type=click.Choice(["event", "interval", "beep", "devices"], case_sensitive=False),
    default="event",
    help="Mode of operation. Default is `event`. \n\n"
    "- `event`  : Process events based on triggers or keyboard "
    "events like `5`, `q`, `ESC`.\n\n"
    "- `interval` : Operate and produce QR codes in fixed time "
    "intervals.\n\n"
    "- `beep`     : Generate beep sound for test purposes.\n\n"
    "- `devices`  : List available audio devices info.",
)
@click.option(
    "-o",
    "--output-prefix",
    default="output_",
    type=str,
    help="Output log file name prefix.",
)
@click.option(
    "-w",
    "--windowed",
    is_flag=True,
    default=False,
    help="Run script in windowed mode, by default fullscreen mode is used.",
)
@click.option(
    "-z",
    "--size",
    "win_size",
    type=(int, int),
    default=(1920, 1080),
    help="Specify window size as a tuple of integers (default: 1920 1080)."
    "Used only in windowed mode.",
)
@click.option(
    "-d",
    "--display",
    default=1,
    type=int,
    help="Specify display number as an integer (default: 1).",
)
@click.option(
    "-s",
    "--qr-scale",
    default=0.8,
    type=float,
    help="Specify QR code scale factor in range 0..1. "
    "Use 1.0 to fit full height (default: 0.8).",
)
@click.option(
    "-r",
    "--qr-duration",
    default=0.5,
    type=float,
    help="Specifies QR code and possibly audio code (NFE) "
    "duration in seconds. Default is 0.5 sec.",
)
@click.option(
    "-y",
    "--qr-async",
    is_flag=True,
    default=False,
    help="Use async QR code generation (default is False). In async "
    "mode script doesn't wait for the end of QR code presentation "
    "(controlled by `qr_duration` parameter) and break current "
    "QR code and display the new one. Can be used for testing "
    "purposes or MRI scans with very short or irregular TR "
    "intervals.",
)
@click.option(
    "-a",
    "--audio-lib",
    type=click.Choice(
        ["psychopy_sounddevice", "psychopy_ptb", "sounddevice"], case_sensitive=True
    ),
    default="psychopy_sounddevice",
    help="Specify audio library to be used. Default is `psychopy_sounddevice`.",
)
@click.option(
    "-c",
    "--audio-codec",
    type=click.Choice(["FSK", "NFE"], case_sensitive=True),
    default="FSK",
    help="Specify audio codec to produce audio code. Default is `FSK`.",
)
@click.option(
    "-u",
    "--mute",
    is_flag=True,
    default=False,
    help="Disable audio codes generation (default is False).",
)
@click.option(
    "-t", "--trials", default=300, type=int, help="Specifies number of trials."
)
@click.option(
    "-d",
    "--duration",
    default=-1,
    type=float,
    help="Specifies script duration in seconds. Use negative value "
    "for infinite duration (default: -1).",
)
@click.option(
    "-i",
    "--interval",
    default=2,
    type=float,
    help="Specifies interval value (default: 2.0).",
)
@click.option(
    "-k",
    "--keep-audiocode",
    is_flag=True,
    default=False,
    help="Store audiocode as separate .wav files "
    "for debug purposes (default is False).",
)
@click.pass_context
def timesync_stimuli(
    ctx,
    mode: str,
    output_prefix: str,
    windowed: bool,
    win_size: tuple[int, int],
    display: int,
    qr_scale: float,
    qr_duration: float,
    qr_async: bool,
    audio_lib: str,
    audio_codec: str,
    mute: bool,
    trials: int,
    duration: float,
    interval: float,
    keep_audiocode: bool,
):
    """Run psychopy script with QR video and audio codes."""
    click.echo("reprostim timesync-stimuli")

    from ..qr.timesync_stimuli import do_init, do_main, get_output_file_name

    is_fullscreen: bool = not windowed

    # psychopy has similar logging levels like
    # default logging module
    # pl.console.setLevel(log_level)
    start_ts: datetime = datetime.now()
    logger.debug("reprostim timesync-stimuli script started")
    logger.debug(f"  Started on   : {start_ts}")
    logger.debug(f"    mode       : {mode}")
    logger.debug(f"    prefix     : {output_prefix}")
    logger.debug(f"    fullscreen : {is_fullscreen}")
    logger.debug(f"    win_size   : {win_size[0]}x{win_size[1]}")
    logger.debug(f"    display    : {display}")
    logger.debug(f"    audio_lib  : {audio_lib}")
    logger.debug(f"    mute       : {mute}")
    logger.debug(f"    duration   : {duration}")
    logger.debug(f"    qr duration: {qr_duration}")
    logger.debug(f"    qr async   : {qr_async}")
    logger.debug(f"    interval   : {interval}")

    output: str = get_output_file_name(output_prefix, start_ts)
    logger.debug(f"    output     : {output}")

    # setup environment variables
    os.environ["REPROSTIM_AUDIO_LIB"] = audio_lib

    if not do_init(output):
        logger.error()
        return -1

    res = do_main(
        mode,
        output,
        is_fullscreen,
        win_size,
        display,
        qr_scale,
        qr_duration,
        qr_async,
        audio_codec,
        mute,
        trials,
        duration,
        interval,
        keep_audiocode,
        click.echo,
    )

    end_ts: datetime = datetime.now()
    logger.debug(f"  Finished on: {end_ts}")

    # rename log file if any
    output2: str = get_output_file_name(output_prefix, start_ts, end_ts)
    if os.path.exists(output):
        os.rename(output, output2)
        logger.info(f"Output log renamed: {output} -> {output2}")

    logger.info(f"reprostim timesync-stimuli script finished: {res}")
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {res}")
    return res
