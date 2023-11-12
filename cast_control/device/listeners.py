from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Final, override

from mpris_server import EventAdapter, Server
from pychromecast.controllers.media import MediaStatus, MediaStatusListener
from pychromecast.controllers.receiver import CastStatus, CastStatusListener, LaunchErrorListener, LaunchFailure
from pychromecast.socket_client import ConnectionStatus, ConnectionStatusListener

from ..adapter import DeviceAdapter
from ..base import Device, Status


log: Final[logging.Logger] = logging.getLogger(__name__)


# status with volume attributes
VolumeStatus = MediaStatus | CastStatus


class DeviceEventListenerBase(
  CastStatusListener,
  ConnectionStatusListener,
  LaunchErrorListener,
  MediaStatusListener,
  ABC
):
  """Event listeners that conform to PyChromecast's API"""

  @abstractmethod
  def load_media_failed(self, item: int, error_code: int):
    pass

  @abstractmethod
  def new_cast_status(self, status: CastStatus):
    pass

  @abstractmethod
  def new_connection_status(self, status: ConnectionStatus):
    pass

  @abstractmethod
  def new_launch_error(self, status: LaunchFailure):
    pass

  @abstractmethod
  def new_media_status(self, status: MediaStatus):
    pass


class DeviceEventAdapter(EventAdapter):
  name: str
  device: Device
  server: Server
  adapter: DeviceAdapter | None

  @override
  def __init__(
    self,
    name: str,
    device: Device,
    server: Server,
    adapter: DeviceAdapter | None = None
  ):
    self.name = name
    self.device = device
    self.server = server
    self.adapter = adapter

    super().__init__(root=self.server.root, player=self.server.player)


class DeviceEventListener(
  DeviceEventAdapter,
  DeviceEventListenerBase
):
  def _update_volume(self, status: Status):
    if isinstance(status, VolumeStatus):
      self.on_volume()

  def _update_metadata(self, status: Status | None = None):
    if status:
      self._update_volume(status)

    # wire up mpris_server with cc events
    self.on_player_all()
    self.on_root_all()
    # self.on_playback()
    # self.on_options()

    # wire up local integration with mpris
    self.adapter.on_new_status()

  @override
  def new_media_status(self, status: MediaStatus):
    log.debug(f'Handling new media status: {status}')
    self._update_metadata(status)

  @override
  def new_cast_status(self, status: CastStatus):
    log.debug(f'Handling new cast status: {status}')
    self._update_metadata(status)

  @override
  def new_connection_status(self, status: ConnectionStatus):
    log.info(f'Handling new connection status: {status}')
    self._update_metadata(status)

  @override
  def new_launch_error(self, status: LaunchFailure):
    log.error(f'Handling new launch error: {status}')
    self._update_metadata(status)

  @override
  def load_media_failed(self, item: int, error_code: int):
    log.error(f'Load media failed: {error_code=}, {item=}')
    self._update_metadata()


def register_event_listener(
  device: Device,
  server: Server,
  adapter: DeviceAdapter
):
  event_listener = DeviceEventListener(device.name, device, server, adapter)

  device.register_connection_listener(event_listener)
  device.register_launch_error_listener(event_listener)
  device.register_status_listener(event_listener)
  device.media_controller.register_status_listener(event_listener)
