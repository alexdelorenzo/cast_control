import logging
import sys

from mpris_server import server

from .base import get_chromecast
from .adapter import ChromecastAdapter
from .listeners import register_mpris_adapter


logging.basicConfig(level=logging.WARN)


def register_adapters_and_listeners():
  chromecast = get_chromecast(name="KILLA")

  if not chromecast:
    logging.warning("Chromecast not found.")
    sys.exit(1)

  chromecast_adapter = ChromecastAdapter(chromecast)
  mpris = server.Server(name=chromecast.name,
                        adapter=chromecast_adapter)
  mpris.publish()

  register_mpris_adapter(chromecast, mpris, chromecast_adapter)


def main():
  from gi.repository import GLib

  register_adapters_and_listeners()
  loop = GLib.MainLoop()
  loop.run()


if __name__ == "__main__":
  # from dbus.mainloop.glib import DBusGMainLoop
  # DBusGMainLoop(set_as_default=True)

  main()
