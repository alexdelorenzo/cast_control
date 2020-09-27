from typing import Optional
import logging
import sys

from mpris_server.server import Server

from .base import get_chromecast, RC_NO_CHROMECAST
from .adapter import ChromecastAdapter
from .listeners import register_mpris_adapter


def create_adapters_and_server(chromecast_name: Optional[str]) -> Optional[Server]:
  if chromecast_name:
    chromecast = get_chromecast(chromecast_name)
  
  else:
    chromecast = get_chromecast()

  if not chromecast:
    return

  chromecast_adapter = ChromecastAdapter(chromecast)
  mpris = Server(name=chromecast.name, adapter=chromecast_adapter)
  mpris.publish()

  register_mpris_adapter(chromecast, mpris, chromecast_adapter)

  return mpris


def main(name: Optional[str], log_level: int = logging.INFO):
  logging.basicConfig(level=log_level)
  mpris = create_adapters_and_server(name)

  if not mpris:
    logging.warning("Chromecast not found.")
    sys.exit(RC_NO_CHROMECAST)

  mpris.loop()


if __name__ == "__main__":
  main(sys.argv[1])
