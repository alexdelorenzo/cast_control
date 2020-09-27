from mimetypes import guess_type
from pathlib import Path
from typing import List, Dict

from pychromecast import Chromecast
from gi.overrides.GLib import Variant

from mpris_server.adapters import Metadata, PlayState, MprisAdapter, \
  Microseconds, VolumeDecimal, RateDecimal, Track, Album, Artist
from mpris_server.base import URI, MIME_TYPES, BEGINNING, DEFAULT_RATE, DbusObj
from mpris_server.compat import get_dbus_name

from .base import ChromecastMediaType, ChromecastWrapper, DEFAULT_THUMB, \
  NO_DURATION, NO_DELTA, DESKTOP_FILE

US_IN_SEC = 1_000_000  # seconds to microseconds
DEFAULT_TRACK = "/track/1"


class ChromecastAdapter(MprisAdapter):
  def __init__(self, chromecast: Chromecast):
    self.cc = ChromecastWrapper(chromecast)
    super().__init__(chromecast.name)

  def get_uri_schemes(self) -> List[str]:
    return URI

  def get_mime_types(self) -> List[str]:
    return MIME_TYPES

  def can_quit(self) -> bool:
    return True

  def quit(self):
    self.cc.quit_app()

  def get_current_position(self) -> Microseconds:
    position_secs = self.cc.media_status.adjusted_current_time

    if position_secs:
      return int(position_secs * US_IN_SEC)

    return BEGINNING

  def next(self):
    self.cc.media_controller.queue_next()

  def previous(self):
    self.cc.media_controller.queue_prev()

  def pause(self):
    self.cc.media_controller.pause()

  def resume(self):
    self.play()

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

  def seek(self, time: Microseconds):
    seconds = int(time / US_IN_SEC)
    self.cc.media_controller.seek(seconds)

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

  def get_rate(self) -> RateDecimal:
    return DEFAULT_RATE

  def set_rate(self, val: RateDecimal):
    pass

  def get_shuffle(self) -> bool:
    return False

  def set_shuffle(self, val: bool):
    return False

  def get_art_url(self, track: int = None) -> str:
    thumb = self.cc.media_controller.thumbnail
    return thumb if thumb else DEFAULT_THUMB

  def get_volume(self) -> VolumeDecimal:
    return self.cc.cast_status.volume_level

  def set_volume(self, val: VolumeDecimal):
    curr = self.get_volume()
    diff = val - curr

    # can't adjust vol by 0
    if diff > NO_DELTA:  # vol up
      self.cc.volume_up(diff)

    elif diff < NO_DELTA:
      self.cc.volume_down(abs(diff))

  def is_mute(self) -> bool:
    if self.cc.cast_status:
      return self.cc.cast_status.volume_muted

  def set_mute(self, val: bool):
    self.cc.set_volume_muted(val)

  def can_go_next(self) -> bool:
    return self.cc.media_status.supports_queue_next

  def can_go_previous(self) -> bool:
    return self.cc.media_status.supports_queue_prev

  def can_play(self) -> bool:
    return True

  def can_pause(self) -> bool:
    return self.cc.media_status.supports_pause

  def can_seek(self) -> bool:
    return self.cc.media_status.supports_seek

  def can_control(self) -> bool:
    return True

  def get_stream_title(self) -> str:
    title = self.cc.media_controller.title
    metadata = self.cc.media_status.media_metadata

    if 'subtitle' in metadata:
      title = ' - '.join((title, metadata['subtitle']))

    return title

  def get_previous_track(self) -> Track:
    pass

  def get_next_track(self) -> Track:
    pass

  def _get_duration(self) -> Microseconds:
    duration = self.cc.media_status.duration

    if duration:
      duration *= US_IN_SEC

    else:
      duration = NO_DURATION

    return duration

  def metadata(self) -> Metadata:
    title: str = self.get_stream_title()
    dbus_name: DbusObj = f"/track/{get_dbus_name(title)}"

    artist: str = self.cc.media_status.artist
    artists: List[str] = [artist] if artist else []
    comments: List[str] = []

    metadata = {
      "mpris:trackid": dbus_name,
      "mpris:length": self._get_duration(),
      "mpris:artUrl": self.get_art_url(),
      "xesam:url": self.cc.media_status.content_id,
      "xesam:title": title,
      "xesam:artist": artists,
      "xesam:album": self.cc.media_status.album_name,
      "xesam:albumArtist": artists,
      "xesam:discNumber": 1,
      "xesam:trackNumber": self.cc.media_status.track,
      "xesam:comment": comments,
    }

    return metadata

  def get_current_track(self) -> Track:
    art_url = self.get_art_url()
    content_id = self.cc.media_status.content_id
    name = self.cc.media_status.artist
    duration = self._get_duration()
    artist = Artist(name)

    album = Album(
      name=self.cc.media_status.album_name,
      artists=(artist,),
      art_url=art_url,
    )

    track = Track(
      track_id=DEFAULT_TRACK,
      name=self.get_stream_title(),
      track_no=self.cc.media_status.track,
      length=int(duration),
      uri=content_id,
      artists=(artist,),
      album=album,
      art_url=art_url,
      disc_no=1,
      type=get_media_type(self.cc)
    )

    return track

  def get_desktop_entry(self) -> str:
    return str(Path(DESKTOP_FILE).absolute())


def get_media_type(cc: ChromecastWrapper) -> ChromecastMediaType:
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


