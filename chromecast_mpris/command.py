from typing import Optional
import logging
import sys 

import click

from .base import Seconds, NoChromecastFoundException, RC_NO_CHROMECAST
from .run import run_server, DEFAULT_WAIT


@click.command(help="Control Chromecasts through MPRIS media controls.")
@click.option('--name', '-n', default=None, show_default=True, type=click.STRING,
              help="Specify a Chromecast name, otherwise control the first Chromecast found.")
@click.option('--log-level', '-l', default=logging.INFO, show_default=True,
              type=click.INT, help='Debugging log level.')
@click.option('--wait', '-w', default=None, show_default=True,
              type=click.INT,
              help="Retry after specified amount of seconds if a Chromecast isn't found.")
def cmd(name: str, log_level: int, wait: Optional[Seconds]):
  try:
    run_server(name, log_level, wait)

  except NoChromecastFoundException as e:
    logging.warning(f"{e} not found")
    sys.exit(RC_NO_CHROMECAST)


if __name__ == "__main__":
  cmd()
