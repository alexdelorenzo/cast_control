from typing import Union, Optional
from abc import ABC, abstractmethod
import logging

from mpris_server.adapters import MprisAdapter
from mpris_server.events import EventAdapter
from mpris_server.server import Server

from pychromecast.controllers.media import MediaStatus, \
  MediaStatusListener
from pychromecast.controllers.receiver import CastStatus, \
  CastStatusListener
from pychromecast.socket_client import ConnectionStatus, \
  ConnectionStatusListener
from pychromecast import Chromecast

from .base import Status


# status with volume attributes
VolumeStatus = Union[MediaStatus, CastStatus]


class DeviceEventListenerBase(
  MediaStatusListener,
  CastStatusListener,
  ConnectionStatusListener,
  ABC
):
  """Event listeners that conform to PyChromecast's API"""

  @abstractmethod
  def new_media_status(self, status: MediaStatus):
    pass

  @abstractmethod
  def new_cast_status(self, status: CastStatus):
    pass

  @abstractmethod
  def new_connection_status(self, status: ConnectionStatus):
    pass


class DeviceEventAdapter(EventAdapter):
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


class DeviceEventListener(
  DeviceEventAdapter,
  DeviceEventListenerBase
):
  def _check_volume(self, status: Status):
    if not isinstance(status, VolumeStatus.__args__):
      return

    vol = status.volume_level
    muted = status.volume_muted

    if vol != self.adapter.get_volume() or \
       muted != self.adapter.is_mute():
      self.on_volume()

  def _update_metadata(self, status: Status):
    self._check_volume(status)

    # wire up mpris_server with cc events
    self.on_playback()
    self.on_options()

    # wire up local integration with mpris
    self.adapter.wrapper.on_new_status()

  def new_media_status(self, status: MediaStatus):
    self._update_metadata(status)

  def new_cast_status(self, status: CastStatus):
    self._update_metadata(status)

  def new_connection_status(self, status: ConnectionStatus):
    self._update_metadata(status)


def register_mpris_adapter(
  chromecast: Chromecast,
  server: Server,
  adapter: MprisAdapter
):
  event_listener = \
    DeviceEventListener(chromecast.name, chromecast, server, adapter)
  chromecast.media_controller.register_status_listener(event_listener)
  chromecast.register_status_listener(event_listener)
