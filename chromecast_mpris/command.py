from typing import Optional
import logging
import sys

import click

from .base import NoChromecastFoundException, \
  RC_NO_CHROMECAST, LOG_LEVEL, DEFAULT_RETRY_WAIT
from .run import run_server


HELP: str = """
Control casting devices via Linux media controls and desktops.

This daemon connects your casting device directly to the D-Bus media player interface.
"""


@click.command(help=HELP)
@click.option('--name', '-n', default=None, show_default=True, type=click.STRING,
  help="Connect to a device via its name, otherwise control the first device found.")
@click.option('--host', '-h', default=None, show_default=True, type=click.STRING,
  help="Connect to a device via its hostname or IP address, otherwise control the first device found.")
@click.option('--uuid', '-u', default=None, show_default=True, type=click.STRING,
  help="Connect to a device via its UUID, otherwise control the first device found\n")
@click.option('--wait', '-w', default=None, show_default=True, type=click.FLOAT,
  help="Seconds to wait between trying to make initial successful connections to a device.")
@click.option('--retry-wait', '-r',
  default=DEFAULT_RETRY_WAIT, show_default=True, type=click.FLOAT,
  help="Seconds to wait between reconnection attempts if a successful connection is interrupted.")
@click.option('--icon', '-i', is_flag=True,
  default=False, show_default=True, type=click.BOOL,
  help="Use a lighter icon instead of the dark icon. The lighter icon goes well with dark themes.")
@click.option('--log-level', '-l', default=LOG_LEVEL, show_default=True, type=click.STRING,
  help='Set the debugging log level.')
def cmd(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[float],
  retry_wait: Optional[float],
  icon: bool,
  log_level: str
):
  try:
    run_server(
      name,
      host,
      uuid,
      wait,
      retry_wait,
      icon,
      log_level
    )

  except NoChromecastFoundException as e:
    logging.warning(f"{e} not found")
    sys.exit(RC_NO_CHROMECAST)


if __name__ == "__main__":
  cmd()
