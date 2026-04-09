# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

import logging
import time

import click

# setup logging
logger = logging.getLogger(__name__)


@click.command(
    help="Utility to parse video `*.mkv` recorded by "
    "`reprostim-videocapture` utility and locate "
    "integrated QR time codes."
)
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-m",
    "--mode",
    default="PARSE",
    type=click.Choice(["PARSE", "INFO"]),
    show_default=True,
    help="Specify execution mode. Default is `PARSE`, "
    "normal execution. "
    "Use `INFO` to dump video file info like duration, "
    "bitrate, file size etc, (in this case "
    "`PATH` argument specifies video file or directory "
    "containing video files).",
)
@click.option(
    "-g",
    "--grayscale",
    default="opencv",
    type=click.Choice(["none", "numpy", "opencv"]),
    show_default=True,
    help="Grayscale conversion method applied to each frame before QR decoding. "
    "`opencv` uses cv2.cvtColor (fast, recommended). "
    "`numpy` uses np.mean (slow, legacy). "
    "`none` passes raw frame as is — may cause errors with some decoders.",
)
@click.option(
    "-x",
    "--scale",
    default=1.0,
    type=click.FloatRange(min=0.0, min_open=True, max=1.0),
    show_default=True,
    help="Frame downscale factor in (0, 1]. At 0.5 frame area is reduced to 25%, "
    "cutting decode cost. At 1.0 (default) no resize is applied.",
)
@click.pass_context
def qr_parse(ctx, path: str, mode: str, grayscale: str, scale: float):
    """Parse QR codes in captured videos."""

    from ..qr.qr_parse import do_main

    logger.debug("qr_parse(...)")

    start_time_sec = time.time()

    res = do_main(
        path=path, mode=mode, grayscale=grayscale, scale=scale, out_func=click.echo
    )

    elapsed_sec = round(time.time() - start_time_sec, 1)
    logger.debug(f"Command 'qr-parse' completed in {elapsed_sec} sec, exit code {res}")
    return res
