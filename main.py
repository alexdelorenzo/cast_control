from dbus.mainloop.glib import DBusGMainLoop
from mpris_server import server

from .base import get_chromecast
from .adapter import ChromecastAdapter
from .listeners import register_mpris_adapter

import logging
import time
import sys


logging.basicConfig(level=logging.DEBUG)
DBusGMainLoop(set_as_default=True)


def main():
  chromecast = get_chromecast(name="KILLA")

  if not chromecast:
    print("Chromecast not found.")
    sys.exit(1)

  chromecast_adapter = ChromecastAdapter(chromecast)
  mpris = server.Server(adapter=chromecast_adapter)
  mpris.publish()

  register_mpris_adapter(chromecast, mpris)
  time.sleep(10_000_000)
