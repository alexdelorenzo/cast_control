import logging
import sys

from mpris_server import server

from .base import get_chromecast, RC_NO_CHROMECAST
from .adapter import ChromecastAdapter
from .listeners import register_mpris_adapter


def register_adapters_and_listeners(name: str) -> server.Server:
  chromecast = get_chromecast(name)

  if not chromecast:
    logging.warning("Chromecast not found.")
    sys.exit(RC_NO_CHROMECAST)

  chromecast_adapter = ChromecastAdapter(chromecast)
  mpris = server.Server(name=chromecast.name,
                        adapter=chromecast_adapter)
  mpris.publish()

  register_mpris_adapter(chromecast, mpris, chromecast_adapter)

  return mpris


def main(name: str, log_level: int = logging.INFO):
  logging.basicConfig(level=log_level)

  mpris = register_adapters_and_listeners(name)
  mpris.loop()


if __name__ == "__main__":
  # from dbus.mainloop.glib import DBusGMainLoop
  # DBusGMainLoop(set_as_default=True)

  main(sys.argv[1])
