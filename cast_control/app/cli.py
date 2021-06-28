from __future__ import annotations
from typing import Optional, NamedTuple, Any
import collections
import logging
import sys

import click

from .. import __version__, __author__, __copyright__,\
  __license__, HOMEPAGE, ENTRYPOINT_NAME, CLI_MODULE_NAME
from ..base import RC_NO_CHROMECAST, LOG_LEVEL, NAME, \
  DEFAULT_RETRY_WAIT, RC_NOT_RUNNING, LOG, RC_OK
from ..types import Final
from .daemon import MprisDaemon, DaemonArgs, get_daemon, \
  get_daemon_from_args
from .run import run_safe


assert __name__ == CLI_MODULE_NAME


LOG_MODE: Final[str] = 'r'
LOG_END: Final[str] = ''

VERSION_INFO: Final[str] = f'{NAME} v{__version__}'

NOT_RUNNING_MSG: Final[str] = "Daemon isn't running."
HELP: Final[str] = f'''
Control casting devices via Linux media controls and desktops.

This daemon connects your casting device to the D-Bus media player interface (MPRIS).

See {HOMEPAGE} for more information.
'''


class CliArgs(NamedTuple):
  args: tuple[str, ...]
  kwargs: dict[str, Any]


NAME_ARGS: Final[CliArgs] = CliArgs(
  args=('--name', '-n'),
  kwargs=dict(
    default=None,
    show_default=True,
    type=click.STRING,
    help="Connect to a device via its name, otherwise control the first device found."
  )
)

HOST_ARGS: Final[CliArgs] = CliArgs(
  args=('--host', '-h'),
  kwargs=dict(
    default=None,
    show_default=True,
    type=click.STRING,
    help="Connect to a device via its hostname or IP address, otherwise control the first device found."
  )
)

UUID_ARGS: Final[CliArgs] = CliArgs(
  args=('--uuid', '-u'),
  kwargs=dict(
    default=None,
    show_default=True,
    type=click.STRING,
    help="Connect to a device via its UUID, otherwise control the first device found."
  )
)

WAIT_ARGS: Final[CliArgs] = CliArgs(
  args=('--wait', '-w'),
  kwargs=dict(
    default=None,
    show_default=True,
    type=click.FLOAT,
    help="Seconds to wait between trying to make initial successful connections to a device."
  )
)

RETRY_ARGS: Final[CliArgs] = CliArgs(
  args=('--retry-wait', '-r'),
  kwargs=dict(
    default=DEFAULT_RETRY_WAIT,
    show_default=True,
    type=click.FLOAT,
    help="Seconds to wait between reconnection attempts if a successful connection is interrupted."
  )
)

ICON_ARGS: Final[CliArgs] = CliArgs(
  args=('--icon', '-i'),
  kwargs=dict(
    is_flag=True,
    default=False,
    show_default=True,
    type=click.BOOL,
    help="Use a lighter icon instead of the dark icon. The lighter icon goes well with dark themes."
  )
)

LOG_ARGS: Final[CliArgs] = CliArgs(
  args=('--log-level', '-l'),
  kwargs=dict(
    default=LOG_LEVEL,
    show_default=True,
    type=click.STRING,
    help='Set the debugging log level.'
  )
)


# see https://alexdelorenzo.dev/notes/click
class OrderAsCreated(click.Group):
  '''List `click` commands in the order they're declared.'''

  def list_commands(self, ctx: click.Context) -> list[str]:
    return list(self.commands)


@click.group(help=HELP, invoke_without_command=True)
@click.option('--license', '-L',
  is_flag=True, default=False, type=click.BOOL,
  help="Show license and copyright information.")
@click.option('--version', '-V',
  is_flag=True, default=False, type=click.BOOL,
  help="Show version information.")
@click.pass_context
def cli(
  ctx: click.Context,
  license: bool,
  version: bool,
):
  if license:
    click.echo(__copyright__)

  if version:
    click.echo(VERSION_INFO)

  if license or version:
    sys.exit(RC_OK)

  elif ctx.invoked_subcommand:
    return

  help: str = cli.get_help(ctx)
  click.echo(help)


assert cli.name == ENTRYPOINT_NAME


@cli.command(
  help='Connect to a device and run the service in the foreground.',
)
@click.option(*NAME_ARGS.args, **NAME_ARGS.kwargs)
@click.option(*HOST_ARGS.args, **HOST_ARGS.kwargs)
@click.option(*UUID_ARGS.args, **UUID_ARGS.kwargs)
@click.option(*WAIT_ARGS.args, **WAIT_ARGS.kwargs)
@click.option(*RETRY_ARGS.args, **RETRY_ARGS.kwargs)
@click.option(*ICON_ARGS.args, **ICON_ARGS.kwargs)
@click.option(*LOG_ARGS.args, **LOG_ARGS.kwargs)
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
    log_level,
    set_logging=True
  )

  run_safe(args)


@cli.group(
  cls=OrderAsCreated,
  help='Connect, disconnect or reconnect the background service to or from your device.',
)
def service():
  pass


@service.command(
  help='Connect the background service to a device.'
)
@click.option(*NAME_ARGS.args, **NAME_ARGS.kwargs)
@click.option(*HOST_ARGS.args, **HOST_ARGS.kwargs)
@click.option(*UUID_ARGS.args, **UUID_ARGS.kwargs)
@click.option(*WAIT_ARGS.args, **WAIT_ARGS.kwargs)
@click.option(*RETRY_ARGS.args, **RETRY_ARGS.kwargs)
@click.option(*ICON_ARGS.args, **ICON_ARGS.kwargs)
@click.option(*LOG_ARGS.args, **LOG_ARGS.kwargs)
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
  args.save()

  try:
    daemon = get_daemon_from_args(run_safe, args)
    daemon.start()

  except Exception as e:
    logging.exception(e)
    logging.warning("Error launching daemon.")

    args.delete()


@service.command(
  help='Disconnect the background service from the device.'
)
def disconnect():
  daemon = get_daemon()

  if not daemon.pid:
    logging.warning(NOT_RUNNING_MSG)
    sys.exit(RC_NOT_RUNNING)

  daemon.stop()
  DaemonArgs.delete()


@service.command(
  help='Reconnect the background service to the device.'
)
def reconnect():
  daemon: Optional[MprisDaemon] = None
  args = DaemonArgs.load()

  if args:
    daemon = get_daemon_from_args(run_safe, args)

  if not args or not daemon.pid:
    logging.warning(NOT_RUNNING_MSG)
    sys.exit(RC_NOT_RUNNING)

  daemon.restart()


@service.command(
  help='Show the service log.'
)
def log():
  click.echo(f"<Log file: {LOG}>")

  # a large log could hang Python or the system
  # iterate over the file instead of using Path.read_text()
  with LOG.open(LOG_MODE) as log:
    for line in log:
      print(line, end=LOG_END)


if __name__ == "__main__":
  cli()
