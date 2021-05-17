from typing import Union, Optional
from abc import ABC, abstractmethod
import logging

from mpris_server.adapters import MprisAdapter
from mpris_server.events import EventAdapter
from mpris_server.server import Server

from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatus
from pychromecast import Chromecast

from .base import Status


class ChromecastEventListener(ABC):
  """
  Event listeners that conform to pychromecast's API
  """

  @abstractmethod
  def new_media_status(self, status: MediaStatus):
    pass

  @abstractmethod
  def new_cast_status(self, status: CastStatus):
    pass


class ChromecastEventAdapter(EventAdapter):
  def __init__(
    self,
    name: str,
    chromecast: Chromecast,
    server: Server,
    adapter: Optional[MprisAdapter] = None
  ):
    self.name = name
    self.chromecast = chromecast
    self.server = server
    self.adapter = adapter
    self.cc = chromecast
    super().__init__(self.server.player, self.server.root)


class ChromecastEventHandler(
  ChromecastEventAdapter,
  ChromecastEventListener
):
  def check_volume(self, status: Status):
    vol = status.volume_level
    muted = status.volume_muted

    if vol != self.adapter.get_volume() \
       or muted != self.adapter.is_mute():
      self.on_volume()

  def new_media_status(self, status: MediaStatus):
    self.check_volume(status)
    self.on_playback()
    self.on_options()

    self.adapter.wrapper.on_new_status()

  def new_cast_status(self, status: CastStatus):
    self.check_volume(status)


def register_mpris_adapter(
  chromecast: Chromecast,
  server: Server,
  adapter: MprisAdapter
):
  event_listener = \
    ChromecastEventHandler(chromecast.name, chromecast, server, adapter)
  chromecast.media_controller.register_status_listener(event_listener)
  chromecast.register_status_listener(event_listener)
