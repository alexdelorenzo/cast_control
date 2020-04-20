from abc import ABC

import pychromecast
from pychromecast.controllers.media import MediaStatus
from pychromecast.socket_client import CastStatus

from mpris_server import server, adapter
from mpris_server.player import dbus_emit_changes


class DbusEventAdapter:
  def __init__(self,
               name: str,
               chromecast: pychromecast.Chromecast,
               server: server.Server = None,
               adapter: 'Adapter' = None):
    self.name = name
    self.chromecast = chromecast
    self.server = server

    self.adapter = adapter
    self.player = self.server.player
    self.cc = chromecast

  def on_ended(self):
    dbus_emit_changes(self.player, ['PlaybackStatus'])

  def on_volume(self):
    dbus_emit_changes(self.player, ['Volume', 'Metadata'])

  def on_playback(self):
    dbus_emit_changes(self.player, ['PlaybackStatus', 'Metadata'])

  def on_playpause(self):
    dbus_emit_changes(self.player, ['PlaybackStatus'])

  def on_title(self):
    dbus_emit_changes(self.player, ['Metadata'])

  def on_seek(self, position: float):
    ms = position * 1000
    self.player.Seeked(ms)

  def on_options(self):
    dbus_emit_changes(self.player,
                      ['LoopStatus', 'Shuffle, CanGoPrevious', 'CanGoNext'])


class ChromecastEventListener(ABC):
  def new_media_status(self, status: MediaStatus):
    pass

  def new_cast_status(self, status: CastStatus):
    pass


class CastEventMprisAdapter(DbusEventAdapter,
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
                           adapter: adapter.Adapter):
  listenerMedia = CastEventMprisAdapter(chromecast.name,
                                        chromecast,
                                        server,
                                        adapter)
  chromecast.media_controller.register_status_listener(listenerMedia)
  chromecast.register_status_listener(listenerMedia)


