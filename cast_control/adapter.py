from __future__ import annotations

from mpris_server.adapters import Metadata, PlayState, MprisAdapter, \
  Microseconds, VolumeDecimal, RateDecimal, PlayerAdapter, RootAdapter
from mpris_server.base import URI, MIME_TYPES, DEFAULT_RATE, DbusObj, \
  Track

from .base import Device
from .types import Protocol, runtime_checkable
from .device.wrapper import DeviceWrapper


@runtime_checkable
class DeviceIntegration(Protocol):
  wrapper: DeviceWrapper

  def set_icon(self, light_icon: bool):
    self.wrapper.set_icon(light_icon)

  def on_new_status(self, *args, **kwargs):
    self.wrapper.on_new_status(*args, **kwargs)


class DeviceRootAdapter(DeviceIntegration, RootAdapter):
  def get_uri_schemes(self) -> list[str]:
    return URI

  def get_mime_types(self) -> list[str]:
    return MIME_TYPES

  def get_desktop_entry(self) -> str:
    return self.wrapper.get_desktop_entry()

  def can_quit(self) -> bool:
    return self.wrapper.can_quit()

  def quit(self):
    self.wrapper.quit()


class DevicePlayerAdapter(DeviceIntegration, PlayerAdapter):
  def can_go_next(self) -> bool:
    return self.wrapper.can_play_next()

  def can_go_previous(self) -> bool:
    return self.wrapper.can_play_prev()

  def can_play(self) -> bool:
    return self.wrapper.can_play()

  def can_pause(self) -> bool:
    return self.wrapper.can_pause()

  def can_seek(self) -> bool:
    return self.wrapper.can_seek()

  def can_control(self) -> bool:
    return self.wrapper.can_control()

  def get_current_position(self) -> Microseconds:
    return self.wrapper.get_current_position()

  def next(self):
    self.wrapper.next()

  def previous(self):
    self.wrapper.previous()

  def pause(self):
    self.wrapper.pause()

  def resume(self):
    self.play()

  def stop(self):
    self.wrapper.stop()

  def play(self):
    self.wrapper.play()

  def get_playstate(self) -> PlayState:
    return self.wrapper.get_playstate()

  def seek(
    self,
    time: Microseconds,
    track_id: Optional[DbusObj] = None
  ):
    self.wrapper.seek(time)

  def open_uri(self, uri: str):
    self.wrapper.open_uri(uri)

  def is_repeating(self) -> bool:
    return self.wrapper.is_repeating()

  def is_playlist(self) -> bool:
    return self.wrapper.is_playlist()

  def get_rate(self) -> RateDecimal:
    return self.wrapper.get_rate()

  def set_rate(self, val: RateDecimal):
    pass

  def get_shuffle(self) -> bool:
    return False

  def set_shuffle(self, val: bool):
    pass

  def get_art_url(self, track: int = None) -> str:
    return self.wrapper.get_art_url(track)

  def get_volume(self) -> VolumeDecimal:
    return self.wrapper.get_volume()

  def set_volume(self, val: VolumeDecimal):
    self.wrapper.set_volume(val)

  def is_mute(self) -> bool:
    return self.wrapper.is_mute()

  def set_mute(self, val: bool):
    self.wrapper.set_mute(val)

  def get_stream_title(self) -> str:
    return self.wrapper.get_stream_title()

  def get_duration(self) -> Microseconds:
    return self.wrapper.get_duration()

  def metadata(self) -> Metadata:
    return self.wrapper.metadata()

  def get_current_track(self) -> Track:
    return self.wrapper.get_current_track()

  def add_track(
    self,
    uri: str,
    after_track: DbusObj,
    set_as_current: bool
  ):
    self.wrapper.add_track(uri, after_track, set_as_current)

  def can_edit_track(self) -> bool:
    return self.wrapper.can_edit_track()

  def set_repeating(self, val: bool):
    pass

  def set_loop_status(self, val: str):
    pass

  def get_previous_track(self) -> Track:
    pass

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
