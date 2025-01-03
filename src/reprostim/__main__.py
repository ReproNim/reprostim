# SPDX-FileCopyrightText: 2024-present ReproNim <info@repronim.org>
#
# SPDX-License-Identifier: MIT
import sys

if __name__ == "__main__":
    from .cli.entrypoint import main

    sys.exit(main())
