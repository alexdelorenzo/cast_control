from __future__ import annotations

from typing import override

from mpris_server import (
  DbusObj, LoopStatus, MIME_TYPES, Metadata, Microseconds, MprisAdapter, PlayState,
  PlayerAdapter, Rate, RootAdapter, Track, TrackListAdapter, URI, Volume,
)

from .base import Device
from .device.wrapper import DeviceWrapper
from .protocols import DeviceIntegration


class DeviceRootAdapter(DeviceIntegration, RootAdapter):
  @override
  def can_quit(self) -> bool:
    return self.wrapper.can_quit()

  @override
  def get_desktop_entry(self) -> str:
    return self.wrapper.get_desktop_entry()

  @override
  def get_mime_types(self) -> list[str]:
    return MIME_TYPES

  @override
  def get_uri_schemes(self) -> list[str]:
    return URI

  @override
  def has_tracklist(self) -> bool:
    return self.wrapper.has_tracklist()

  @override
  def quit(self):
    self.wrapper.quit()


class DevicePlayerAdapter(DeviceIntegration, PlayerAdapter):
  @override
  def can_control(self) -> bool:
    return self.wrapper.can_control()

  @override
  def can_go_next(self) -> bool:
    return self.wrapper.can_play_next()

  @override
  def can_go_previous(self) -> bool:
    return self.wrapper.can_play_prev()

  @override
  def can_pause(self) -> bool:
    return self.wrapper.can_pause()

  @override
  def can_play(self) -> bool:
    return self.wrapper.can_play()

  @override
  def can_seek(self) -> bool:
    return self.wrapper.can_seek()

  @override
  def get_art_url(self, track: int = None) -> str:
    return self.wrapper.get_art_url(track)

  @override
  def get_current_position(self) -> Microseconds:
    return self.wrapper.get_current_position()

  @override
  def get_current_track(self) -> Track:
    return self.wrapper.get_current_track()

  @override
  def get_next_track(self) -> Track:
    return self.wrapper.get_next_track()

  @override
  def get_playstate(self) -> PlayState:
    return self.wrapper.get_playstate()

  @override
  def get_previous_track(self) -> Track:
    return self.wrapper.get_previous_track()

  @override
  def get_rate(self) -> Rate:
    return self.wrapper.get_rate()

  @override
  def get_shuffle(self) -> bool:
    return False

  @override
  def get_stream_title(self) -> str:
    return self.wrapper.get_stream_title()

  @override
  def get_volume(self) -> Volume:
    return self.wrapper.get_volume()

  @override
  def is_mute(self) -> bool:
    return self.wrapper.is_mute()

  @override
  def is_playlist(self) -> bool:
    return self.wrapper.is_playlist()

  @override
  def is_repeating(self) -> bool:
    return self.wrapper.is_repeating()

  @override
  def metadata(self) -> Metadata:
    return self.wrapper.metadata()

  @override
  def next(self):
    self.wrapper.next()

  @override
  def open_uri(self, uri: str):
    self.wrapper.open_uri(uri)

  @override
  def pause(self):
    self.wrapper.pause()

  @override
  def play(self):
    self.wrapper.play()

  @override
  def previous(self):
    self.wrapper.previous()

  @override
  def resume(self):
    self.play()

  @override
  def seek(self, time: Microseconds, track_id: DbusObj | None = None):
    self.wrapper.seek(time)

  @override
  def set_icon(self, lighter: bool = False):
    self.wrapper.set_icon(lighter)

  @override
  def set_loop_status(self, value: LoopStatus):
    pass

  @override
  def set_mute(self, value: bool):
    self.wrapper.set_mute(value)

  @override
  def set_rate(self, value: Rate):
    pass

  @override
  def set_repeating(self, value: bool):
    pass

  @override
  def set_shuffle(self, value: bool):
    pass

  @override
  def set_volume(self, value: Volume):
    self.wrapper.set_volume(value)

  @override
  def stop(self):
    self.wrapper.stop()


class DeviceTrackListAdapter(DeviceIntegration, TrackListAdapter):
  @override
  def add_track(self, uri: str, after_track: DbusObj, set_as_current: bool):
    self.wrapper.add_track(uri, after_track, set_as_current)

  @override
  def can_edit_tracks(self) -> bool:
    return self.wrapper.can_edit_tracks()

  @override
  def get_tracks(self) -> list[DbusObj]:
    return self.wrapper.get_tracks()


class DeviceAdapter(MprisAdapter, DevicePlayerAdapter, DeviceRootAdapter, DeviceTrackListAdapter):
  @override
  def __init__(self, device: Device):
    self.wrapper = DeviceWrapper(device)
    super().__init__(self.wrapper.name)
