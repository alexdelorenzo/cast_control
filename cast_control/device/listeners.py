from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Union, override

from pychromecast.controllers.media import MediaStatus, MediaStatusListener
from pychromecast.controllers.receiver import CastStatus, CastStatusListener
from pychromecast.socket_client import ConnectionStatus, ConnectionStatusListener

from mpris_server import MprisAdapter, EventAdapter, Server

from ..adapter import DeviceAdapter
from ..base import Device, Status


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

  def load_media_failed(self, *args, **kwargs):
    pass


class DeviceEventAdapter(EventAdapter):
  def __init__(
    self,
    name: str,
    device: Device,
    server: Server,
    adapter: Optional[DeviceAdapter] = None
  ):
    self.name = name
    self.dev = device
    self.server = server
    self.adapter = adapter
    super().__init__(self.server.player, self.server.root)


class DeviceEventListener(
  DeviceEventAdapter,
  DeviceEventListenerBase
):
  def _update_volume(self, status: Status):
    if not isinstance(status, VolumeStatus.__args__):
      return

    self.on_volume()

  def _update_metadata(self, status: Status):
    self._update_volume(status)

    # wire up mpris_server with cc events
    # self.on_playback()
    # self.on_options()
    self.on_player_all()
    self.on_root_all()

    # wire up local integration with mpris
    self.adapter.on_new_status()

  @override
  def new_media_status(self, status: MediaStatus):
    self._update_metadata(status)

  @override
  def new_cast_status(self, status: CastStatus):
    self._update_metadata(status)

  @override
  def new_connection_status(self, status: ConnectionStatus):
    self._update_metadata(status)


def register_event_listener(
  device: Device,
  server: Server,
  adapter: DeviceAdapter
):
  event_listener = DeviceEventListener(device.name, device, server, adapter)
  device.media_controller.register_status_listener(event_listener)
  device.register_status_listener(event_listener)
