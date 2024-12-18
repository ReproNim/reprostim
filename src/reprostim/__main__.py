# SPDX-FileCopyrightText: 2024-present Vadim Melnik <vmelnik@docsultant.com>
#
# SPDX-License-Identifier: MIT
import sys

if __name__ == "__main__":
    from .cli.entrypoint import main

    sys.exit(main())
