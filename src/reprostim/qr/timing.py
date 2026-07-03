# SPDX-FileCopyrightText: 2020-2026 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

"""
Display monitoring service and cross-platform API used to list
available GUI displays and monitor information, status and
functionality to automatically attach external command for
certain screen.
"""

import logging

# initialize the logger
logger = logging.getLogger(__name__)
# logging.getLogger().setLevel(logging.DEBUG)
# logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logger.debug(f"name={__name__}")
