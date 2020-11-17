from typing import Optional
import logging
import sys

import click

from .base import Seconds, NoChromecastFoundException, \
  RC_NO_CHROMECAST, LOG_LEVEL
from .run import run_server


@click.command(help="Control Chromecasts through MPRIS media controls.")
@click.option('--name', '-n', default=None, show_default=True, type=click.STRING,
  help="Specify a Chromecast name, otherwise control the first Chromecast found.")
@click.option('--host', '-h', default=None, show_default=True, type=click.STRING,
  help="Hostname or IP address of streaming device.")
@click.option('--wait', '-w', default=None, show_default=True, type=click.INT,
  help="Retry after specified amount of seconds if a Chromecast isn't found.")
@click.option('--log-level', '-l', default=LOG_LEVEL, show_default=True, type=click.STRING,
  help='Debugging log level.')
def cmd(
  name: Optional[str],
  host: Optional[str],
  wait: Optional[Seconds],
  log_level: str
):
  try:
    run_server(name, host, wait, log_level)

  except NoChromecastFoundException as e:
    logging.warning(f"{e} not found")
    sys.exit(RC_NO_CHROMECAST)


if __name__ == "__main__":
  cmd()
