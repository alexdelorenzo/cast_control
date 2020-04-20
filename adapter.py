from typing import List
from mimetypes import guess_type

from main import main
from mpris_server import adapter
import pychromecast

from mpris_server.constants import URI, MIME_TYPES
from mpris_server.player import PlayState


class ChromecastAdapter(adapter.Adapter):
  def __init__(self, chromecast: pychromecast.Chromecast):
    self.chromecast = chromecast
    self.cc = chromecast

  def get_uri_schemes(self) -> List[str]:
    return URI

  def get_mime_types(self) -> List[str]:
    return MIME_TYPES

  def get_current_postion(self) -> int:
    pass

  def next(self):
    self.cc.media_controller.skip()

  def previous(self):
    self.cc.media_controller.queue_prev()

  def pause(self):
    self.cc.media_controller.pause()

  def resume(self):
    self.cc.media_controller.play()

  def stop(self):
    self.cc.media_controller.stop()

  def play(self):
    self.cc.media_controller.play()

  def get_playstate(self) -> PlayState:
    if self.cc.media_controller.is_paused:
      return PlayState.PAUSED

    elif self.cc.media_controller.is_playing:
      return PlayState.PLAYING

    return PlayState.STOPPED

  def seek(self, time: int):
    self.cc.media_controller.seek(time)

  def open_uri(self, uri: str):
    mimetype, _ = guess_type(uri)
    self.cc.media_controller.play_media(uri, mimetype)

  def is_repeating(self) -> bool:
    pass

  def is_playlist(self) -> bool:
    pass

  def set_repeating(self, val: bool):
    pass

  def set_loop_status(self, val: str):
    pass

  def get_rate(self) -> float:
    return 1.0

  def set_rate(self, val: float):
    pass

  def get_shuffle(self) -> bool:
    pass

  def set_shuffle(self, val: bool):
    pass

  def get_art_url(self, track: int) -> str:
    pass

  def get_volume(self) -> int:
    pass

  def set_volume(self, val: int):
    pass

  def is_mute(self) -> bool:
    pass

  def set_mute(self, val: bool):
    pass

  def get_position(self) -> int:
    pass

  def can_go_next(self) -> bool:
    pass

  def can_go_previous(self) -> bool:
    pass

  def can_play(self) -> bool:
    pass

  def can_pause(self) -> bool:
    pass

  def can_seek(self) -> bool:
    pass

  def can_control(self) -> bool:
    pass

    ## needed for metadata

  def metadata(self):
    pass

  def get_stream_title(self) -> str:
    pass

  def get_current_track(self) -> Track:
    pass

  def get_previous_track(self) -> Track:
    pass

  def get_next_track(self) -> Track:
    pass


if __name__ == "__main__":
  main()
