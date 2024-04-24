import logging.config
import sys

import click

logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
logger.debug(f"name={__name__}")


@click.command(help='Utility to determine no-signal frames in '
                    'reprostim-videocapture recorded *.mkv videos.')
def main():
    logger.debug("nosignal.py tool")
    click.echo("Done.")


if __name__ == "__main__":
    main()
