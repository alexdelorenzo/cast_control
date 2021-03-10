from typing import List

from pychromecast import Chromecast

from mpris_server.adapters import Metadata, PlayState, MprisAdapter, \
  Microseconds, VolumeDecimal, RateDecimal
from mpris_server.base import URI, MIME_TYPES, DEFAULT_RATE, DbusObj, \
  Track

from .wrapper import ChromecastWrapper


class ChromecastAdapter(MprisAdapter):
  def __init__(self, chromecast: Chromecast):
    self.wrapper = ChromecastWrapper(chromecast)
    super().__init__(self.wrapper.name)

  def get_uri_schemes(self) -> List[str]:
    return URI

  def get_mime_types(self) -> List[str]:
    return MIME_TYPES

  def can_quit(self) -> bool:
    return True

  def can_go_next(self) -> bool:
    return self.wrapper.can_play_next()

  def can_go_previous(self) -> bool:
    return self.wrapper.can_play_prev()

  def can_play(self) -> bool:
    return True

  def can_pause(self) -> bool:
    return self.wrapper.can_pause()

  def can_seek(self) -> bool:
    return self.wrapper.can_seek()

  def can_control(self) -> bool:
    return True

  def quit(self):
    self.wrapper.quit()

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

  def seek(self, time: Microseconds):
    self.wrapper.seek(time)

  def open_uri(self, uri: str):
    self.wrapper.open_uri(uri)

  def is_repeating(self) -> bool:
    return self.wrapper.is_repeating()

  def is_playlist(self) -> bool:
    return self.wrapper.is_playlist()

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

  def get_previous_track(self) -> Track:
    pass

  def get_next_track(self) -> Track:
    pass

  def get_duration(self) -> Microseconds:
    return self.wrapper.get_duration()

  def metadata(self) -> Metadata:
    return self.wrapper.metadata()

  def get_current_track(self) -> Track:
    return self.wrapper.get_current_track()

  def get_desktop_entry(self) -> str:
    return self.wrapper.get_desktop_entry()

  def add_track(
    self,
    uri: str,
    after_track: DbusObj,
    set_as_current: bool
  ):
    self.wrapper.add_track(uri, after_track, set_as_current)

  def can_edit_track(self):
    return True
