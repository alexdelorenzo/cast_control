from typing import List

from pychromecast import Chromecast

from mpris_server.adapters import Metadata, PlayState, MprisAdapter, \
  Microseconds, VolumeDecimal, RateDecimal, Track
from mpris_server.base import URI, MIME_TYPES, DEFAULT_RATE, DbusObj

from .wrapper import ChromecastWrapper


class ChromecastAdapter(MprisAdapter):
  def __init__(self, chromecast: Chromecast):
    self.adapter = ChromecastWrapper(chromecast)
    super().__init__(chromecast.name)

  def get_uri_schemes(self) -> List[str]:
    return URI

  def get_mime_types(self) -> List[str]:
    return MIME_TYPES

  def can_quit(self) -> bool:
    return True

  def can_go_next(self) -> bool:
    return self.adapter.can_play_next()

  def can_go_previous(self) -> bool:
    return self.adapter.can_play_prev()

  def can_play(self) -> bool:
    return True

  def can_pause(self) -> bool:
    return self.adapter.can_pause()

  def can_seek(self) -> bool:
    return self.adapter.can_seek()

  def can_control(self) -> bool:
    return True

  def quit(self):
    self.adapter.quit()

  def get_current_position(self) -> Microseconds:
    return self.adapter.get_current_position()

  def next(self):
    self.adapter.next()

  def previous(self):
    self.adapter.previous()

  def pause(self):
    self.adapter.pause()

  def resume(self):
    self.play()

  def stop(self):
    self.adapter.stop()

  def play(self):
    self.adapter.play()

  def get_playstate(self) -> PlayState:
    return self.adapter.get_playstate()

  def seek(self, time: Microseconds):
    self.adapter.seek(time)

  def open_uri(self, uri: str):
    self.adapter.open_uri(uri)

  def is_repeating(self) -> bool:
    return self.adapter.is_repeating()

  def is_playlist(self) -> bool:
    return self.adapter.is_playlist()

  def set_repeating(self, val: bool):
    pass

  def set_loop_status(self, val: str):
    pass

  def get_rate(self) -> RateDecimal:
    return DEFAULT_RATE

  def set_rate(self, val: RateDecimal):
    pass

  def get_shuffle(self) -> bool:
    return False

  def set_shuffle(self, val: bool):
    return False

  def get_art_url(self, track: int = None) -> str:
    return self.adapter.get_art_url(track)

  def get_volume(self) -> VolumeDecimal:
    return self.adapter.get_volume()

  def set_volume(self, val: VolumeDecimal):
    self.adapter.set_volume(val)

  def is_mute(self) -> bool:
    return self.adapter.is_mute()

  def set_mute(self, val: bool):
    self.adapter.set_mute(val)

  def get_stream_title(self) -> str:
    return self.adapter.get_stream_title()

  def get_previous_track(self) -> Track:
    pass

  def get_next_track(self) -> Track:
    pass

  def get_duration(self) -> Microseconds:
    return self.adapter.get_duration()

  def metadata(self) -> Metadata:
    return self.adapter.metadata()

  def get_current_track(self) -> Track:
    return self.adapter.get_current_track()

  def get_desktop_entry(self) -> str:
    return self.adapter.get_desktop_entry()

  def add_track(
    self,
    uri: str,
    after_track: DbusObj,
    set_as_current: bool
  ):
    self.adapter.add_track(uri, after_track, set_as_current)

  def can_edit_track(self):
    return True
