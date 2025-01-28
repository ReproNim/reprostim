# SPDX-FileCopyrightText: 2020-2025 ReproNim Team <info@repronim.org>
#
# SPDX-License-Identifier: MIT

try:
    # flake8: noqa: F401
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0"  # Default version

# specify the name of reprostim tool
__reprostim_name__ = "reprostim"
