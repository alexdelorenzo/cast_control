import logging
import sys

from mpris_server.server import Server

from .base import get_chromecast, RC_NO_CHROMECAST
from .adapter import ChromecastAdapter
from .listeners import register_mpris_adapter


def create_adapters_and_server(chromecast_name: str) -> Server:
  chromecast = get_chromecast(chromecast_name)

  if not chromecast:
    logging.warning("Chromecast not found.")
    sys.exit(RC_NO_CHROMECAST)

  chromecast_adapter = ChromecastAdapter(chromecast)
  mpris = Server(name=chromecast.name, adapter=chromecast_adapter)
  mpris.publish()

  register_mpris_adapter(chromecast, mpris, chromecast_adapter)

  return mpris


def main(name: str, log_level: int = logging.INFO):
  logging.basicConfig(level=log_level)

  mpris = create_adapters_and_server(name)
  mpris.loop()


if __name__ == "__main__":
  # from dbus.mainloop.glib import DBusGMainLoop
  # DBusGMainLoop(set_as_default=True)

  main(sys.argv[1])
