from __future__ import annotations
from typing import Optional, Callable, NamedTuple
import logging
import pickle
import sys

import click

from .base import NoChromecastFoundException, \
  RC_NO_CHROMECAST, LOG_LEVEL, DEFAULT_RETRY_WAIT, \
  DATA_DIR, NAME, ARGS, NO_DEVICE, RC_NOT_RUNNING
from .run import get_daemon, run_safe, MprisDaemon


HELP: str = f"""
Control casting devices via Linux media controls and desktops.

This daemon connects your casting device directly to the D-Bus media player interface.
"""


class DaemonArgs(NamedTuple):
  name: Optional[str]
  host: Optional[str]
  uuid: Optional[str]
  wait: Optional[float]
  retry_wait: Optional[float]
  icon: bool
  log_level: str

  @property
  def file(self) -> Path:
    name, host, uuid, *_ = self
    device = name or host or uuid or NO_DEVICE

    return ARGS.with_stem(f'{device}-args')

  @staticmethod
  def load() -> Optional[DaemonArgs]:
    if ARGS.exists():
      dump = ARGS.read_bytes()
      return pickle.loads(dump)

    return None

  @staticmethod
  def delete():
    if ARGS.exists():
      ARGS.unlink()

  def save(self) -> Path:
    dump = pickle.dumps(self)
    ARGS.write_bytes(dump)


@click.group(help=HELP)
def cmd():
  pass


@cmd.command(
  help='Connect to the device and run the service in the foreground.',
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
  args = DaemonArgs(
    name,
    host,
    uuid,
    wait,
    retry_wait,
    icon,
    log_level
  )

  run_safe(*args)


@cmd.group(
  help='Connect, disconnect or reconnect the background service to or from your device.'
)
def service():
  pass


@service.command(
  help='Connect the background service to the device.'
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
  args = DaemonArgs(
    name,
    host,
    uuid,
    wait,
    retry_wait,
    icon,
    log_level
  )
  daemon = get_daemon(run_safe, *args)

  daemon.start()
  args.save()


@service.command(
  help='Disconnect the background service from the device.'
)
def disconnect():
  daemon = get_daemon()

  daemon.stop()
  DaemonArgs.delete()


@service.command(
  help='Reconnect the background service to the device.'
)
def reconnect():
  daemon: Optional[MprisDaemon] = None
  args = DaemonArgs.load()

  if args:
    daemon = get_daemon(run_safe, *args)

  if not args or not daemon.pid:
    logging.warn("Daemon isn't running.")
    sys.exit(RC_NOT_RUNNING)

  daemon.restart()


if __name__ == "__main__":
  cmd()
