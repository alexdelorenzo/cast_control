from typing import Optional, Callable
from pathlib import Path
from functools import partial
import logging
import sys

import click
from daemons.prefab.run import RunDaemon
from daemons import daemonizer

from .base import NoChromecastFoundException, \
  RC_NO_CHROMECAST, LOG_LEVEL, DEFAULT_RETRY_WAIT, \
  DATA_DIR, NAME
from .run import run_server


RC_NOT_RUNNING: int = 3
PID: Path = DATA_DIR / f'{NAME}.pid'

HELP: str = """
Control casting devices via Linux media controls and desktops.

This daemon connects your casting device directly to the D-Bus media player interface.
"""


FuncMaybe = Optional[Callable]


class MprisDaemon(RunDaemon):
  target: FuncMaybe = None

  def set_target(self, func: FuncMaybe = None, *args, **kwargs):
    if not func:
      self.target = None
      return

    self.target = partial(func, *args, **kwargs)

  def run(self):
    if self.target:
      self.target()


def get_daemon(
  func: FuncMaybe = None,
  *args,
  pidfile: str = str(PID),
  **kwargs
) -> MprisDaemon:
  daemon = MprisDaemon(pidfile=pidfile)
  daemon.set_target(func, *args, **kwargs)

  return daemon


def run_safe(
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
    logging.warning(f"Device {e} not found")
    sys.exit(RC_NO_CHROMECAST)


@click.group(help=HELP)
def cmd():
  pass


@cmd.command(
  help='Run the service locally.',
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
def run(
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
  help='Start, stop or restart the background service.'
)
def service():
  pass


@service.command(
  help='Run the service in the background.'
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
def run(
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
  help='Stop the background service.'
)
def stop():
  daemon = get_daemon()
  daemon.stop()


@service.command(
  help='Restart the background service.'
)
def restart():
  daemon = get_daemon()

  if not daemon.pid:
    logging.warn("Daemon isn't running.")
    sys.exit(RC_NOT_RUNNING)

  daemon.restart()


if __name__ == "__main__":
  cmd()
