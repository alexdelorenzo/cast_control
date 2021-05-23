from typing import Optional, Callable
from time import sleep
from pathlib import Path
from functools import partial
import logging
import sys

from daemons.prefab.run import RunDaemon
from mpris_server.server import Server

from .base import get_chromecast, Seconds, get_chromecast_via_host, \
  NoChromecastFoundException, LOG_LEVEL, get_chromecast_via_uuid, \
  DEFAULT_RETRY_WAIT, NoChromecastFoundException, RC_NO_CHROMECAST, \
  DATA_DIR, NAME, RC_NOT_RUNNING, PID, NO_DEVICE, DEFAULT_WAIT
from .adapter import ChromecastAdapter
from .listeners import register_mpris_adapter


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


def set_log_level(level: str = LOG_LEVEL):
  level = level.upper()
  logging.basicConfig(level=level)


def create_adapters_and_server(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Server]:
  if host:
    chromecast = get_chromecast_via_host(host, retry_wait)

  elif name:
    chromecast = get_chromecast(name, retry_wait)

  elif uuid:
    chromecast = get_chromecast_via_uuid(uuid, retry_wait)

  else:
    chromecast = get_chromecast(retry_wait=retry_wait)

  if not chromecast:
    return None

  chromecast_adapter = ChromecastAdapter(chromecast)
  mpris = Server(name=chromecast.name, adapter=chromecast_adapter)
  mpris.publish()

  register_mpris_adapter(chromecast, mpris, chromecast_adapter)

  return mpris


def retry_until_found(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[Seconds] = DEFAULT_WAIT,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Server]:
  """
    If the Chromecast isn't found, keep trying to find it.

    If `wait` is None, then retrying is disabled.
  """

  while True:
    mpris = create_adapters_and_server(name, host, uuid, retry_wait)

    if mpris or wait is None:
      return mpris

    device = name or host or uuid or NO_DEVICE
    logging.info(f"{device} not found. Waiting {wait} seconds before retrying.")
    sleep(wait)


def run_server(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[float] = DEFAULT_WAIT,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
  icon: bool = False,
  log_level: str = LOG_LEVEL
):
  set_log_level(log_level)
  mpris = retry_until_found(name, host, uuid, wait, retry_wait)

  if mpris and icon:
    mpris.adapter.wrapper.set_icon(True)

  if not mpris:
    device = name or host or uuid or NO_DEVICE
    raise NoChromecastFoundException(device)

  mpris.loop()


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
    logging.warning(f"{e} not found")
    sys.exit(RC_NO_CHROMECAST)
