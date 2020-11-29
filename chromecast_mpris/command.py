from typing import Optional
import logging
import sys

import click

from .base import Seconds, NoChromecastFoundException, \
  RC_NO_CHROMECAST, LOG_LEVEL, DEFAULT_RETRY_WAIT
from .run import run_server


@click.command(help="Control casting devices through MPRIS media controls.")
@click.option('--name', '-n', default=None, show_default=True, type=click.STRING,
  help="Specify a device name, otherwise control the first device found.")
@click.option('--host', '-h', default=None, show_default=True, type=click.STRING,
  help="Hostname or IP address of streaming device.")
@click.option('--uuid', '-u', default=None, show_default=True, type=click.STRING,
  help="Streaming device's UUID.")
@click.option('--wait', '-w', default=None, show_default=True, type=click.INT,
  help="Retry after specified amount of seconds if a device isn't found.")
@click.option('--retry-wait', '-r',
  default=DEFAULT_RETRY_WAIT, show_default=True, type=click.FLOAT,
  help="Seconds to wait between retries to reconnect after a device connection is interrupted.")
@click.option('--log-level', '-l', default=LOG_LEVEL, show_default=True, type=click.STRING,
  help='Debugging log level.')
def cmd(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[Seconds],
  retry_wait: Optional[float],
  log_level: str
):
  try:
    run_server(name, host, uuid, wait, retry_wait, log_level)

  except NoChromecastFoundException as e:
    logging.warning(f"{e} not found")
    sys.exit(RC_NO_CHROMECAST)


if __name__ == "__main__":
  cmd()
