from __future__ import annotations

import logging
import sys
from time import sleep
from typing import Optional

from mpris_server.server import Server

from .daemon import DaemonArgs
from .state import setup_logging
from ..adapter import DeviceAdapter
from ..base import DEFAULT_ICON, DEFAULT_RETRY_WAIT, DEFAULT_SET_LOG, DEFAULT_WAIT, LOG_LEVEL, NO_DEVICE, \
  NoDevicesFound, RC_NO_CHROMECAST, Seconds
from ..device.device import find_device
from ..device.listeners import register_event_listener


def create_adapters_and_server(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Server]:
  device = find_device(name, host, uuid, retry_wait)

  if not device:
    return None

  adapter = DeviceAdapter(device)
  mpris = Server(name=device.name, adapter=adapter)
  mpris.publish()

  register_event_listener(device, mpris, adapter)

  return mpris


def retry_until_found(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[Seconds] = DEFAULT_WAIT,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Server]:
  """
    If the device isn't found, keep trying to find it.

    If `wait` is None, then retrying is disabled.
  """

  while True:
    mpris = create_adapters_and_server(name, host, uuid, retry_wait)

    if mpris or wait is None:
      return mpris

    device = name or host or uuid or NO_DEVICE
    logging.info(f'{device} not found. Waiting {wait} seconds before retrying.')
    sleep(wait)


def run_server(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[Seconds] = DEFAULT_WAIT,
  retry_wait: Optional[Seconds] = DEFAULT_RETRY_WAIT,
  icon: bool = DEFAULT_ICON,
  log_level: str = LOG_LEVEL,
  set_logging: bool = DEFAULT_SET_LOG,
):
  if set_logging:
    setup_logging(log_level)

  mpris = retry_until_found(name, host, uuid, wait, retry_wait)

  if mpris and icon:
    mpris.adapter: DeviceAdapter
    mpris.adapter.set_icon(True)

  if not mpris:
    device = name or host or uuid or NO_DEVICE
    raise NoDevicesFound(device)

  mpris.loop()


def run_safe(
  args: DaemonArgs
):
  try:
    run_server(*args)

  except NoDevicesFound as e:
    logging.warning(f'{e} not found')
    sys.exit(RC_NO_CHROMECAST)
