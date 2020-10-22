from typing import Union, Optional
from abc import ABC
import logging

from mpris_server.adapters import EventAdapter, MprisAdapter
from mpris_server.server import Server

from pychromecast.controllers.media import MediaStatus
from pychromecast.socket_client import CastStatus
from pychromecast import Chromecast

from .base import Status


DEBUG_FN = 'chromecast_mpris.txt'

#logging.basicConfig(filename=DEBUG_FN)


class ChromecastEventListener(ABC):
  """
  Event listeners that conform to pychromecast's API
  """
  def new_media_status(self, status: MediaStatus):
    # logging.info(repr(status))
    pass

  def new_cast_status(self, status: CastStatus):
    # logging.info(repr(status))
    pass


class ChromecastEventAdapter(EventAdapter):
  def __init__(self,
               name: str,
               chromecast: Chromecast,
               server: Server,
               adapter: MprisAdapter = None):
    self.name = name
    self.chromecast = chromecast
    self.server = server
    self.adapter = adapter
    self.cc = chromecast
    super().__init__(self.server.player, self.server.root)


class ChromecastEventHandler(ChromecastEventAdapter,
                             ChromecastEventListener):
  def check_volume(self, status: Status):
    vol = status.volume_level
    muted = status.volume_muted

    if vol != self.adapter.get_volume() \
       or muted != self.adapter.is_mute():
      self.on_volume()

  def new_media_status(self, status: MediaStatus):
    super().new_media_status(status)
    self.check_volume(status)
    self.on_playback()
    self.on_options()

  def new_cast_status(self, status: CastStatus):
    super().new_cast_status(status)
    self.check_volume(status)


def register_mpris_adapter(chromecast: Chromecast,
                           server: Server,
                           adapter: MprisAdapter):
  event_listener = \
    ChromecastEventHandler(chromecast.name, chromecast, server, adapter)
  chromecast.media_controller.register_status_listener(event_listener)
  chromecast.register_status_listener(event_listener)
