from typing import Optional
from time import sleep
import logging

from mpris_server.server import Server

from .base import get_chromecast, Seconds, get_chromecast_via_host, \
  NoChromecastFoundException, LOG_LEVEL, get_chromecast_via_uuid, \
  DEFAULT_RETRY_WAIT
from .adapter import ChromecastAdapter
from .listeners import register_mpris_adapter


DEFAULT_WAIT: Seconds = 30
NO_DEVICE = 'Device'


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

    logging.info(f"{name or NO_DEVICE} not found. Waiting {wait} seconds before retrying.")
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
  logging.basicConfig(level=log_level.upper())
  mpris = retry_until_found(name, host, uuid, wait, retry_wait)

  if mpris and icon:
    mpris.adapter.wrapper.set_icon(True)

  if not mpris:
    raise NoChromecastFoundException(name)

  mpris.loop()
