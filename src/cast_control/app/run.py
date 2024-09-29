from __future__ import annotations

import logging
from time import sleep
from typing import Final, NoReturn
from uuid import UUID

from mpris_server import Server

from .daemon import Args, get_name
from .state import setup_logging
from ..adapter import DeviceAdapter
from ..base import DEFAULT_ICON, DEFAULT_RETRY_WAIT, DEFAULT_SET_LOG, DEFAULT_WAIT, LOG_LEVEL, \
  NoDevicesFound, Rc, Seconds
from ..device.device import find_device
from ..device.listeners import EventListener


log: Final[logging.Logger] = logging.getLogger(__name__)


def create_server(
  name: str | None = None,
  host: str | None = None,
  uuid: UUID | str | None = None,
  retry_wait: Seconds | None = DEFAULT_RETRY_WAIT,
) -> Server | None:
  if not (device := find_device(name, host, uuid, retry_wait)):
    return None

  adapter = DeviceAdapter(device)
  server = Server(name, adapter)

  EventListener.register(server, device)
  server.publish()

  return server


def retry_until_found(
  name: str | None = None,
  host: str | None = None,
  uuid: UUID | str | None = None,
  wait: Seconds | None = DEFAULT_WAIT,
  retry_wait: Seconds | None = DEFAULT_RETRY_WAIT,
) -> Server | None | NoReturn:
  """
    If the device isn't found, keep trying to find it.

    If `wait` is None, then retrying is disabled.
  """

  while True:
    if server := create_server(name, host, uuid, retry_wait):
      return server

    elif wait is None:
      return None

    device = get_name(name, host, uuid)
    log.warning(f'{device} not found. Waiting {wait} seconds before retrying.')
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
  background: bool = False,
):
  if set_logging:
    setup_logging(log_level)

  if not (server := retry_until_found(name, host, uuid, wait, retry_wait)):
    device = get_name(name, host, uuid)
    raise NoDevicesFound(device)

  server.adapter.set_icon(icon)
  server.loop(background=background)


def run_safe(args: Args):
  try:
    run_server(*args)

  except NoDevicesFound as e:
    log.error(f'Device {e} not found.')
    quit(Rc.NO_DEVICE)
