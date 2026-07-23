# SPDX-FileCopyrightText: 2020-2026 ReproNim ReproStim Team <reprostim@repronim.org>
#
# SPDX-License-Identifier: MIT
import sys

if __name__ == "__main__":
    from .cli.entrypoint import main

    sys.exit(main())
