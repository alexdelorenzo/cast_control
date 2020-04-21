from abc import ABC

import pychromecast
from pychromecast.controllers.media import MediaStatus
from pychromecast.socket_client import CastStatus

from mpris_server import server, adapters
from mpris_server.adapters import EventAdapter, MprisAdapter


class ChromecastEventAdapter(EventAdapter):
  def __init__(self,
               name: str,
               chromecast: pychromecast.Chromecast,
               server: server.Server = None,
               adapter: MprisAdapter = None):
    self.name = name
    self.chromecast = chromecast
    self.server = server

    self.adapter = adapter
    self.cc = chromecast
    super().__init__(self.server.player)


class ChromecastEventListener(ABC):
  """
  Event listeners that conform to pychromecast's API
  """
  def new_media_status(self, status: MediaStatus):
    pass

  def new_cast_status(self, status: CastStatus):
    pass


class ChromecastEventHandler(ChromecastEventAdapter,
                             ChromecastEventListener):
  def check_volume(self, status):
    vol = status.volume_level
    muted = status.volume_muted

    if vol != self.adapter.get_volume() \
       or muted != self.adapter.is_mute():
      self.on_volume()

  def new_media_status(self, status: MediaStatus):
    self.check_volume(status)
    self.on_playback()

  def new_cast_status(self, status: CastStatus):
    self.check_volume(status)


def register_mpris_adapter(chromecast: pychromecast.Chromecast,
                           server: server.Server,
                           adapter: adapters.MprisAdapter):
  listenerMedia = ChromecastEventHandler(chromecast.name,
                                         chromecast,
                                         server,
                                         adapter)
  chromecast.media_controller.register_status_listener(listenerMedia)
  chromecast.register_status_listener(listenerMedia)
