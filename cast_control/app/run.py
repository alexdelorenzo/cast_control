from __future__ import annotations

import logging
from time import sleep
from typing import Final, NamedTuple, NoReturn, cast
from uuid import UUID

from mpris_server import Server

from .daemon import DaemonArgs
from .state import setup_logging
from ..adapter import DeviceAdapter
from ..base import DEFAULT_ICON, DEFAULT_RETRY_WAIT, DEFAULT_SET_LOG, DEFAULT_WAIT, LOG_LEVEL, NO_DEVICE, \
  NoDevicesFound, RC_NO_CHROMECAST, Seconds
from ..device.device import find_device
from ..device.listeners import DeviceEventListener, register_event_listener


log: Final[logging.Logger] = logging.getLogger(__name__)


class ServerEvents(NamedTuple):
  server: Server
  events: DeviceEventListener


def create_server_and_listener(
  name: str | None = None,
  host: str | None = None,
  uuid: UUID | str | None = None,
  retry_wait: Seconds | None = DEFAULT_RETRY_WAIT,
) -> ServerEvents | None:
  if not (device := find_device(name, host, uuid, retry_wait)):
    return None

  adapter = DeviceAdapter(device)
  server = Server(name=device.name, adapter=adapter)
  server.publish()

  events = register_event_listener(device, server, adapter)

  return ServerEvents(server, events)


def retry_until_found(
  name: str | None = None,
  host: str | None = None,
  uuid: UUID | str | None = None,
  wait: Seconds | None = DEFAULT_WAIT,
  retry_wait: Seconds | None = DEFAULT_RETRY_WAIT,
) -> ServerEvents | None | NoReturn:
  """
    If the device isn't found, keep trying to find it.

    If `wait` is None, then retrying is disabled.
  """

  while True:
    if server_events := create_server_and_listener(name, host, uuid, retry_wait):
      if server_events.server or wait is None:
        return server_events

    device = name or host or uuid or NO_DEVICE
    log.info(f'{device} not found. Waiting {wait} seconds before retrying.')
    sleep(wait)


def run_server(
  name: str | None = None,
  host: str | None = None,
  uuid: UUID | str | None = None,
  wait: Seconds | None = DEFAULT_WAIT,
  retry_wait: Seconds | None = DEFAULT_RETRY_WAIT,
  icon: bool = DEFAULT_ICON,
  log_level: str = LOG_LEVEL,
  set_logging: bool = DEFAULT_SET_LOG,
):
  if set_logging:
    setup_logging(log_level)

  if not (server_events := retry_until_found(name, host, uuid, wait, retry_wait)):
    device = name or host or uuid or NO_DEVICE
    raise NoDevicesFound(device)

  server, _ = server_events
  server.adapter.set_icon(icon)
  server.loop()


def run_safe(args: DaemonArgs):
  try:
    run_server(*args)

  except NoDevicesFound as e:
    log.error(f'Device {e} not found.')
    quit(RC_NO_CHROMECAST)
