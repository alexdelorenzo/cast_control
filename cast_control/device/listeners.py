from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Final, Self, override

from mpris_server import EventAdapter, Server
from pychromecast.controllers.media import MediaStatus, MediaStatusListener
from pychromecast.controllers.receiver import CastStatus, CastStatusListener, LaunchErrorListener, LaunchFailure
from pychromecast.socket_client import ConnectionStatus, ConnectionStatusListener

from ..adapter import DeviceAdapter
from ..base import Device, Status


log: Final[logging.Logger] = logging.getLogger(__name__)


# status with volume attributes
VolumeStatus = MediaStatus | CastStatus


class BaseEventListener(
  CastStatusListener,
  ConnectionStatusListener,
  LaunchErrorListener,
  MediaStatusListener,
  ABC
):
  """Event listeners that conform to PyChromecast's API"""

  @override
  @abstractmethod
  def load_media_failed(self, item: int, error_code: int):
    pass

  @override
  @abstractmethod
  def new_cast_status(self, status: CastStatus):
    pass

  @override
  @abstractmethod
  def new_connection_status(self, status: ConnectionStatus):
    pass

  @override
  @abstractmethod
  def new_launch_error(self, status: LaunchFailure):
    pass

  @override
  @abstractmethod
  def new_media_status(self, status: MediaStatus):
    pass


class BaseEventAdapter(EventAdapter):
  server: Server
  device: Device

  name: str
  adapter: DeviceAdapter | None

  @override
  def __init__(self, server: Server, device: Device):
    self.server = server
    self.device = device

    self.name = self.device.name
    self.adapter = self.server.adapter

    super().__init__(
      root=self.server.root,
      player=self.server.player,
      tracklist=self.server.tracklist,
      playlists=self.server.playlists,
    )

  @classmethod
  def register(cls: type[Self], server: Server, device: Device) -> Self:
    events = cls(server, device)
    events.set_and_register()

    return events

  def set_and_register(self):
    self.server.set_event_adapter(self)


class EventListener(BaseEventAdapter, BaseEventListener):
  def _update_volume(self, status: Status | None = None):
    if isinstance(status, VolumeStatus):
      self.on_volume()

  def _update_metadata(self, status: Status | None = None):
    self._update_volume(status)

    # wire up local integration with mpris
    self.adapter.on_new_status()

    # wire up mpris_server with cc events
    self.on_root_all()
    self.on_player_all()
    self.on_tracklist_all()
    # self.on_playlists_all()
    # self.emit_all()

  @override
  def set_and_register(self):
    super().set_and_register()
    register_event_listener(self, self.device)

  @override
  def load_media_failed(self, item: int, error_code: int):
    log.error(f'Load media failed: {error_code=}, {item=}')
    self._update_metadata()

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
  def new_media_status(self, status: MediaStatus):
    log.debug(f'Handling new media status: {status}')
    self._update_metadata(status)


def register_event_listener[E: BaseEventListener](events: E, device: Device):
  device.register_connection_listener(events)
  device.register_launch_error_listener(events)
  device.register_status_listener(events)
  device.media_controller.register_status_listener(events)
