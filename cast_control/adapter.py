from __future__ import annotations

from typing import Optional, override

from mpris_server import (
  Metadata, MprisAdapter, PlayState, PlayerAdapter, Rate, RootAdapter,
  Volume, DbusObj, MIME_TYPES, Track, URI, Microseconds
)
from .base import Device
from .device.wrapper import DeviceWrapper
from .types import Protocol, runtime_checkable


@runtime_checkable
class DeviceIntegration(Protocol):
  wrapper: DeviceWrapper

  def set_icon(self, light_icon: bool):
    self.wrapper.set_icon(light_icon)

  def on_new_status(self, *args, **kwargs):
    self.wrapper.on_new_status(*args, **kwargs)


class DeviceRootAdapter(DeviceIntegration, RootAdapter):
  @override
  def get_uri_schemes(self) -> list[str]:
    return URI

  @override
  def get_mime_types(self) -> list[str]:
    return MIME_TYPES

  @override
  def get_desktop_entry(self) -> str:
    return self.wrapper.get_desktop_entry()

  @override
  def can_quit(self) -> bool:
    return self.wrapper.can_quit()

  @override
  def quit(self):
    self.wrapper.quit()


class DevicePlayerAdapter(DeviceIntegration, PlayerAdapter):
  @override
  def can_go_next(self) -> bool:
    return self.wrapper.can_play_next()

  @override
  def can_go_previous(self) -> bool:
    return self.wrapper.can_play_prev()

  @override
  def can_play(self) -> bool:
    return self.wrapper.can_play()

  @override
  def can_pause(self) -> bool:
    return self.wrapper.can_pause()

  @override
  def can_seek(self) -> bool:
    return self.wrapper.can_seek()

  @override
  def can_control(self) -> bool:
    return self.wrapper.can_control()

  @override
  def get_current_position(self) -> Microseconds:
    return self.wrapper.get_current_position()

  @override
  def next(self):
    self.wrapper.next()

  @override
  def previous(self):
    self.wrapper.previous()

  @override
  def pause(self):
    self.wrapper.pause()

  @override
  def resume(self):
    self.play()

  @override
  def stop(self):
    self.wrapper.stop()

  @override
  def play(self):
    self.wrapper.play()

  @override
  def get_playstate(self) -> PlayState:
    return self.wrapper.get_playstate()

  @override
  def seek(
    self,
    time: Microseconds,
    track_id: Optional[DbusObj] = None
  ):
    self.wrapper.seek(time)

  @override
  def open_uri(self, uri: str):
    self.wrapper.open_uri(uri)

  @override
  def is_repeating(self) -> bool:
    return self.wrapper.is_repeating()

  @override
  def is_playlist(self) -> bool:
    return self.wrapper.is_playlist()

  @override
  def get_rate(self) -> Rate:
    return self.wrapper.get_rate()

  @override
  def set_rate(self, val: Rate):
    pass

  @override
  def get_shuffle(self) -> bool:
    return False

  @override
  def set_shuffle(self, val: bool):
    pass

  @override
  def get_art_url(self, track: int = None) -> str:
    return self.wrapper.get_art_url(track)

  @override
  def get_volume(self) -> Volume:
    return self.wrapper.get_volume()

  @override
  def set_volume(self, val: Volume):
    self.wrapper.set_volume(val)

  @override
  def is_mute(self) -> bool:
    return self.wrapper.is_mute()

  @override
  def set_mute(self, val: bool):
    self.wrapper.set_mute(val)

  @override
  def get_stream_title(self) -> str:
    return self.wrapper.get_stream_title()

  @override
  def get_duration(self) -> Microseconds:
    return self.wrapper.get_duration()

  @override
  def metadata(self) -> Metadata:
    return self.wrapper.metadata()

  @override
  def get_current_track(self) -> Track:
    return self.wrapper.get_current_track()

  @override
  def add_track(
    self,
    uri: str,
    after_track: DbusObj,
    set_as_current: bool
  ):
    self.wrapper.add_track(uri, after_track, set_as_current)

  @override
  def can_edit_track(self) -> bool:
    return self.wrapper.can_edit_track()

  @override
  def set_repeating(self, val: bool):
    pass

  @override
  def set_loop_status(self, val: str):
    pass

  @override
  def get_previous_track(self) -> Track:
    pass

  @override
  def get_next_track(self) -> Track:
    pass


class DeviceAdapter(
  MprisAdapter,
  DevicePlayerAdapter,
  DeviceRootAdapter,
):
  def __init__(self, device: Device):
    self.wrapper = DeviceWrapper(device)
    super().__init__(self.wrapper.name)
