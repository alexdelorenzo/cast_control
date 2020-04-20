from mpris_server import server

from .base import get_chromecast
from .adapter import ChromecastAdapter
from .listeners import register_mpris_adapter

import logging
import sys

from gi.repository import GLib

logging.basicConfig(level=logging.INFO)


def register_adapters_and_listeners():
  chromecast = get_chromecast(name="KILLA")

  if not chromecast:
    print("Chromecast not found.")
    sys.exit(1)

  chromecast_adapter = ChromecastAdapter(chromecast)
  mpris = server.Server(adapter=chromecast_adapter)
  mpris.publish()

  register_mpris_adapter(chromecast, mpris, chromecast_adapter)


def main():
  register_adapters_and_listeners()
  loop = GLib.MainLoop()
  loop.run()


if __name__ == "__main__":
  from dbus.mainloop.glib import DBusGMainLoop
  # DBusGMainLoop(set_as_default=True)

  main()
