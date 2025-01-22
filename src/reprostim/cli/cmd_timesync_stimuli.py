# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import os
from datetime import datetime

import click

from ..qr.timesync_stimuli import Mode, do_init, do_main, get_output_file_name

# setup logging
logger = logging.getLogger(__name__)


@click.command(help="PsychoPy reprostim timesync-stimuli script.")
@click.option(
    "-m",
    "--mode",
    type=click.Choice([mode.value for mode in Mode], case_sensitive=False),
    default=Mode.EVENT,
    help="Mode of operation: event, interval, or beep.",
)
@click.option(
    "-o",
    "--output-prefix",
    default="output_",
    type=str,
    help="Output log file name prefix.",
)
@click.option(
    "-d",
    "--display",
    default=1,
    type=int,
    help="Display number as an integer (default: 1).",
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
    "-a",
    "--audio-lib",
    type=click.Choice(
        ["psychopy_sounddevice", "psychopy_ptb", "sounddevice"], case_sensitive=True
    ),
    default="psychopy_sounddevice",
    help="Specify audio library to be used " "(default: psychopy_sounddevice).",
)
@click.option(
    "-c",
    "--audio-codec",
    type=click.Choice(["FSK", "NFE"], case_sensitive=True),
    default="FSK",
    help="Specify audio codec to produce audio code " "(default: FSK).",
)
@click.option(
    "-m",
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
    default=2,
    type=float,
    help="Specifies script duration in seconds.",
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
    display: int,
    qr_scale: float,
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

    # psychopy has similar logging levels like
    # default logging module
    # pl.console.setLevel(log_level)
    start_ts: datetime = datetime.now()
    logger.debug("reprostim timesync-stimuli script started")
    logger.debug(f"  Started on : {start_ts}")
    logger.debug(f"    mode     : {mode}")
    logger.debug(f"    prefix   : {output_prefix}")
    logger.debug(f"    display  : {display}")
    logger.debug(f"    audio_lib: {audio_lib}")
    logger.debug(f"    mute     : {mute}")
    logger.debug(f"    duration : {duration}")
    logger.debug(f"    interval : {interval}")

    output: str = get_output_file_name(output_prefix, start_ts)
    logger.debug(f"    output   : {output}")

    # setup environment variables
    os.environ["REPROSTIM_AUDIO_LIB"] = audio_lib

    if not do_init(output):
        logger.error()
        return -1

    res = do_main(
        mode,
        output,
        display,
        qr_scale,
        audio_codec,
        mute,
        trials,
        duration,
        interval,
        keep_audiocode,
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
