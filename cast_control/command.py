from typing import Optional, Callable
import logging
import sys

from daemons.prefab.run import RunDaemon
import click

from .base import NoChromecastFoundException, \
  RC_NO_CHROMECAST, LOG_LEVEL, DEFAULT_RETRY_WAIT, \
  DATA_DIR, NAME
from .run import get_daemon, run_safe


HELP: str = """
Control casting devices via Linux media controls and desktops.

This daemon connects your casting device directly to the D-Bus media player interface.
"""


@click.group(help=HELP)
def cmd():
  pass


@cmd.command(
  help='Run the service in the foreground.',
)
@click.option('--name', '-n',
  default=None, show_default=True, type=click.STRING,
  help="Connect to a device via its name, otherwise control the first device found.")
@click.option('--host', '-h',
  default=None, show_default=True, type=click.STRING,
  help="Connect to a device via its hostname or IP address, otherwise control the first device found.")
@click.option('--uuid', '-u',
  default=None, show_default=True, type=click.STRING,
  help="Connect to a device via its UUID, otherwise control the first device found.")
@click.option('--wait', '-w',
  default=None, show_default=True, type=click.FLOAT,
  help="Seconds to wait between trying to make initial successful connections to a device.")
@click.option('--retry-wait', '-r',
  default=DEFAULT_RETRY_WAIT, show_default=True, type=click.FLOAT,
  help="Seconds to wait between reconnection attempts if a successful connection is interrupted.")
@click.option('--icon', '-i',
  is_flag=True, default=False, show_default=True, type=click.BOOL,
  help="Use a lighter icon instead of the dark icon. The lighter icon goes well with dark themes.")
@click.option('--log-level', '-l',
  default=LOG_LEVEL, show_default=True, type=click.STRING,
  help='Set the debugging log level.')
def connect(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[float],
  retry_wait: Optional[float],
  icon: bool,
  log_level: str
):
  run_safe(
    name,
    host,
    uuid,
    wait,
    retry_wait,
    icon,
    log_level
  )


@cmd.group(
  help='Connect or disconnect the background service to/from your device.'
)
def service():
  pass


@service.command(
  help='Connect the background service from the device.'
)
@click.option('--name', '-n',
  default=None, show_default=True, type=click.STRING,
  help="Connect to a device via its name, otherwise control the first device found.")
@click.option('--host', '-h',
  default=None, show_default=True, type=click.STRING,
  help="Connect to a device via its hostname or IP address, otherwise control the first device found.")
@click.option('--uuid', '-u',
  default=None, show_default=True, type=click.STRING,
  help="Connect to a device via its UUID, otherwise control the first device found.")
@click.option('--wait', '-w',
  default=None, show_default=True, type=click.FLOAT,
  help="Seconds to wait between trying to make initial successful connections to a device.")
@click.option('--retry-wait', '-r',
  default=DEFAULT_RETRY_WAIT, show_default=True, type=click.FLOAT,
  help="Seconds to wait between reconnection attempts if a successful connection is interrupted.")
@click.option('--icon', '-i',
  is_flag=True, default=False, show_default=True, type=click.BOOL,
  help="Use a lighter icon instead of the dark icon. The lighter icon goes well with dark themes.")
@click.option('--log-level', '-l',
  default=LOG_LEVEL, show_default=True, type=click.STRING,
  help='Set the debugging log level.')
def connect(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[float],
  retry_wait: Optional[float],
  icon: bool,
  log_level: str
):
  daemon = get_daemon(
    run_safe,
    name,
    host,
    uuid,
    wait,
    retry_wait,
    icon,
    log_level
  )

  daemon.start()


@service.command(
  help='Disconnect the background service from the device.'
)
def disconnect():
  daemon = get_daemon()
  daemon.stop()


#@service.command(
  #help='Restart the background service.'
#)
#def reconnect():
  #daemon = get_daemon()

  #if not daemon.pid:
    #logging.warn("Daemon isn't running.")
    #sys.exit(RC_NOT_RUNNING)

  #daemon.restart()


if __name__ == "__main__":
  cmd()
