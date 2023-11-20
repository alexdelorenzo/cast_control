from __future__ import annotations

import logging
from typing import Final, NamedTuple

import click

from .daemon import Args, MprisDaemon, get_daemon, get_daemon_from_args
from .run import run_safe
from .. import CLI_MODULE_NAME, ENTRYPOINT_NAME, HOMEPAGE, __copyright__, __version__
from ..base import DEFAULT_DEVICE_NAME, DEFAULT_RETRY_WAIT, LOG, LOG_LEVEL, NAME, Rc, Seconds


assert __name__ == CLI_MODULE_NAME


log: Final[logging.Logger] = logging.getLogger(__name__)

LOG_MODE: Final[str] = 'r'
LOG_END: Final[str] = ''

VERSION_INFO: Final[str] = f'{NAME} v{__version__}'

NOT_RUNNING_MSG: Final[str] = "Daemon isn't running."
HELP: Final[str] = f'''
Control casting devices via Linux media controls and desktops.

This daemon connects your casting device to the D-Bus media player interface (MPRIS).

See {HOMEPAGE} for more information.
'''


type KwargsVal = bool | str | int | float | click.ParamType


class CliArgs(NamedTuple):
  args: tuple[str, ...]
  kwargs: dict[str, KwargsVal]


NAME_ARGS: Final[CliArgs] = CliArgs(
  args=('--name', '-n'),
  kwargs=dict(
    default=DEFAULT_DEVICE_NAME,
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
  """List `click` commands in the order they're declared."""

  def list_commands(self, ctx: click.Context) -> list[str]:
    return list(self.commands)


@click.group(
  help=HELP,
  invoke_without_command=True
)
@click.option(
  '--license', '-L',
  is_flag=True, default=False, type=click.BOOL,
  help="Show license and copyright information."
)
@click.option(
  '--version', '-V',
  is_flag=True, default=False, type=click.BOOL,
  help="Show version information."
)
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
    quit(Rc.OK)

  elif ctx.invoked_subcommand:
    return

  help: str = cli.get_help(ctx)
  click.echo(help)


assert cli.name == ENTRYPOINT_NAME


@cli.command(help='Connect to a device and run the service in the foreground.')
@click.option(*NAME_ARGS.args, **NAME_ARGS.kwargs)
@click.option(*HOST_ARGS.args, **HOST_ARGS.kwargs)
@click.option(*UUID_ARGS.args, **UUID_ARGS.kwargs)
@click.option(*WAIT_ARGS.args, **WAIT_ARGS.kwargs)
@click.option(*RETRY_ARGS.args, **RETRY_ARGS.kwargs)
@click.option(*ICON_ARGS.args, **ICON_ARGS.kwargs)
@click.option(*LOG_ARGS.args, **LOG_ARGS.kwargs)
def connect(
  name: str | None,
  host: str | None,
  uuid: str | None,
  wait: Seconds | None,
  retry_wait: Seconds | None,
  icon: bool,
  log_level: str
):
  args = Args(name, host, uuid, wait, retry_wait, icon, log_level, set_logging=True)
  run_safe(args)


@cli.group(
  cls=OrderAsCreated,
  help='Connect, disconnect or reconnect the background service to or from your device.',
)
def service():
  pass


@service.command(help='Connect the background service to a device.')
@click.option(*NAME_ARGS.args, **NAME_ARGS.kwargs)
@click.option(*HOST_ARGS.args, **HOST_ARGS.kwargs)
@click.option(*UUID_ARGS.args, **UUID_ARGS.kwargs)
@click.option(*WAIT_ARGS.args, **WAIT_ARGS.kwargs)
@click.option(*RETRY_ARGS.args, **RETRY_ARGS.kwargs)
@click.option(*ICON_ARGS.args, **ICON_ARGS.kwargs)
@click.option(*LOG_ARGS.args, **LOG_ARGS.kwargs)
def connect(
  name: str | None,
  host: str | None,
  uuid: str | None,
  wait: Seconds | None,
  retry_wait: Seconds | None,
  icon: bool,
  log_level: str
):
  args = Args(name, host, uuid, wait, retry_wait, icon, log_level)
  args.save()

  try:
    daemon = get_daemon_from_args(run_safe, args)
    daemon.start()

  except Exception as e:
    log.exception(e)
    log.error("Error launching daemon.")

    args.delete()


@service.command(help='Disconnect the background service from the device.')
def disconnect():
  daemon = get_daemon()

  if not daemon.pid:
    log.error(NOT_RUNNING_MSG)
    quit(Rc.NOT_RUNNING)

  daemon.stop()
  Args.delete()


@service.command(help='Reconnect the background service to the device.')
def reconnect():
  daemon: MprisDaemon | None = None
  args = Args.load()

  if args:
    daemon = get_daemon_from_args(run_safe, args)

  if not args or not daemon.pid:
    log.error(NOT_RUNNING_MSG)
    quit(Rc.NOT_RUNNING)

  daemon.restart()


@service.command(help='Show the service log.')
def log():
  click.echo(f"<Log file: {LOG}>")

  # a large log could hang Python or the system
  # iterate over the file instead of using Path.read_text()
  with LOG.open(LOG_MODE) as file:
    for line in file:
      print(line, end=LOG_END)


if __name__ == "__main__":
  cli()
