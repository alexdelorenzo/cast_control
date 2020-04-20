from pprint import pprint

import pychromecast

from base import ChromecastState
from mpris_server import server


class CastStatusListener:
  def on_volume_changed(self):
    pass


class ChromecastEventListener:
  def new_media_status(self, status):
    pass

  def new_cast_status(self, status):
    pass


class ChromecastEventMprisAdapter:
  def __init__(self,
               name: str,
               cast: pychromecast.Chromecast,
               server: server.Server = None):
    self.name = name
    self.cast = cast
    self.server = server

    self.state = ChromecastState(name=name)

  @property
  def server(self):
    return self._server

  @server.setter
  def server(self, val: 'server.Server'):
    self._server = val

    if not server:
      return

    self.root = val.root
    self.player = val.player

  def new_media_status(self, status):
    pprint(status.__dict__)

  def new_cast_status(self, status):
    vol = status.volume_level
    muted = status.volume_muted


def register_mpris_adapter(chromecast: pychromecast.Chromecast,
                           server: server.Server):
  listenerMedia = ChromecastEventMprisAdapter(chromecast.name,
                                              chromecast,
                                              server)
  chromecast.media_controller.register_status_listener(listenerMedia)
  chromecast.register_status_listener(listenerMedia)