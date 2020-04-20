from typing import List
from mimetypes import guess_type

from mpris_server import adapter
import pychromecast

from mpris_server.constants import URI, MIME_TYPES
from mpris_server.player import PlayState

from .base import ChromecastMediaType, DEFAULT_THUMB

SEC_TO_US = 1_000_000


class ChromecastAdapter(adapter.Adapter):
  def __init__(self, chromecast: pychromecast.Chromecast):
    self.chromecast = chromecast
    self.cc = chromecast

    super().__init__(chromecast.name, )

  def get_uri_schemes(self) -> List[str]:
    return URI

  def get_mime_types(self) -> List[str]:
    return MIME_TYPES

  def get_current_postion(self) -> int:
    curr = self.cc.media_controller.status.adjusted_current_time

    if curr:
      return int(curr * SEC_TO_US)

    return 0

  def next(self):
    self.cc.media_controller.queue_next()

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
    self.cc.media_controller.seek(int(time / SEC_TO_US))

  def open_uri(self, uri: str):
    mimetype, _ = guess_type(uri)
    self.cc.media_controller.play_media(uri, mimetype)

  def is_repeating(self) -> bool:
    return False

  def is_playlist(self) -> bool:
    return self.can_go_next() or self.can_go_previous()

  def set_repeating(self, val: bool):
    pass

  def set_loop_status(self, val: str):
    pass

  def get_rate(self) -> float:
    return 1.0

  def set_rate(self, val: float):
    pass

  def get_shuffle(self) -> bool:
    return False

  def set_shuffle(self, val: bool):
    return False

  def get_art_url(self, track: int = None) -> str:
    thumb = self.cc.media_controller.thumbnail
    return thumb if thumb else DEFAULT_THUMB

  def get_volume(self) -> int:
    return self.cc.status.volume_level

  def set_volume(self, val: int):
    curr = self.get_volume()
    diff = val - curr

    if diff > 0:  # vol up
      self.cc.volume_up(diff)

    else:
      self.cc.volume_down(abs(diff))

  def is_mute(self) -> bool:
    return self.cc.status.volume_muted

  def set_mute(self, val: bool):
    self.cc.set_volume_muted(val)

  def get_position(self) -> float:
    return self.get_current_postion()

  def can_go_next(self) -> bool:
    return self.cc.media_controller.status.supports_queue_next

  def can_go_previous(self) -> bool:
    return self.cc.media_controller.status.supports_queue_prev

  def can_play(self) -> bool:
    return True

  def can_pause(self) -> bool:
    return self.cc.media_controller.status.supports_pause

  def can_seek(self) -> bool:
    return self.cc.media_controller.status.supports_seek

  def can_control(self) -> bool:
    return True

  def get_stream_title(self) -> str:
    return self.cc.media_controller.title

  def get_current_track(self) -> adapter.Track:
    art_url = self.get_art_url()
    content_id = self.cc.media_controller.status.content_id
    name = self.cc.media_controller.status.artist
    duration = self.cc.media_controller.status.duration

    if duration:
      duration *= SEC_TO_US

    else:
      duration = 0

    artist = adapter.Artist(name)

    album = adapter.Album(
      name=self.cc.media_controller.status.album_name,
      artists=[artist],
      art_url=art_url,
    )

    track = adapter.Track(
      track_id='/tracks/1',
      name=self.get_stream_title(),
      track_no=self.cc.media_controller.status.track,
      length=int(duration),
      uri=content_id,
      artists=[artist],
      album=album,
      art_url=art_url,
      disc_no=1,
      type=get_media_type(self.cc)
    )

    return track

  def get_previous_track(self) -> adapter.Track:
    pass

  def get_next_track(self) -> adapter.Track:
    pass

  def metadata(self):
    pass


def get_media_type(cc: pychromecast.Chromecast):
  if cc.media_controller.status.media_is_movie:
    return ChromecastMediaType.MOVIE
  elif cc.media_controller.status.media_is_tvshow:
    return ChromecastMediaType.TVSHOW
  elif cc.media_controller.status.media_is_photo:
    return ChromecastMediaType.PHOTO
  elif cc.media_controller.status.media_is_musictrack:
    return ChromecastMediaType.MUSICTRACK
  elif cc.media_controller.status.media_is_generic:
    return ChromecastMediaType.GENERIC
