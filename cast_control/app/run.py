from __future__ import annotations
from typing import Optional, Callable
from time import sleep
import logging
import sys

from mpris_server.server import Server

from ..base import Seconds, NoDevicesFound, LOG_LEVEL, \
  DEFAULT_RETRY_WAIT, RC_NO_CHROMECAST, NAME, Device, \
  RC_NOT_RUNNING, NO_DEVICE, DEFAULT_WAIT, \
  DEFAULT_ICON, DEFAULT_SET_LOG
from ..adapter import DeviceAdapter
from ..device.listeners import register_event_listener
from ..device.device import find_device
from .daemon import DaemonArgs
from .state import setup_logging


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
  wait: Optional[float] = DEFAULT_WAIT,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
  icon: bool = DEFAULT_ICON,
  log_level: str = LOG_LEVEL,
  set_logging: bool = DEFAULT_SET_LOG,
):
  if set_logging:
    setup_logging(log_level)

  mpris = retry_until_found(name, host, uuid, wait, retry_wait)

  if mpris and icon:
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
