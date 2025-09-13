# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
API to analyze video files recorded by reprostim-videocapture, along with
their corresponding log files and QR/audio metadata. It extracts key
information about each recording and produces a summary table (videos.tsv)
suitable for quality control, sharing, and further analysis.
"""

import logging
import os

# initialize the logger
# Note: all logs out to stderr
logger = logging.getLogger(__name__)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.debug(f"name={__name__}")


def do_main(path: str, out_func=print):
    logger.debug("video-audit command")
    logger.debug(f"path  : {path}")

    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return 1

    out_func("TODO: analyze")
    return 0
