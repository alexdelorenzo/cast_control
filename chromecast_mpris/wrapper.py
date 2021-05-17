from abc import ABC
from typing import Optional, Any, List, Union, Tuple, \
  NamedTuple, Callable, Set
from pathlib import Path
from mimetypes import guess_type

from pychromecast.controllers.receiver import CastStatus
from pychromecast.controllers.media import MediaStatus, BaseController
from pychromecast.controllers.youtube import YouTubeController
from pychromecast.controllers.spotify import SpotifyController
from pychromecast.controllers.dashcast import DashCastController
# from pychromecast.controllers.homeassistant import HomeAssistantController
# from pychromecast.controllers.plex import PlexApiController, PlexController
from pychromecast import Chromecast

from mpris_server.adapters import Metadata, PlayState, \
  Microseconds, VolumeDecimal, RateDecimal
from mpris_server.base import BEGINNING, DEFAULT_RATE, DbusObj, \
  Track, Album, Artist
from mpris_server.compat import get_dbus_name, enforce_dbus_length

from .base import DEFAULT_THUMB, LIGHT_THUMB, NO_DURATION, NO_DELTA, \
  US_IN_SEC, DEFAULT_DISC_NO, ChromecastMediaType, DESKTOP_FILE_DARK, \
  DESKTOP_FILE_LIGHT, NO_DESKTOP_FILE, NAME


DEFAULT_NAME: str = NAME
NO_ARTIST: str = ''
TITLE_SEP: str = ' - '

YOUTUBE_URLS: Set[str] = {
  'youtube.com/',
  'youtu.be/'
}
YT_LONG, YT_SHORT = YOUTUBE_URLS
YT_VID_URL: str = f'https://{YT_LONG}watch?v='


RESOLUTION: int = 1


class Wrapper(ABC):
  cc: Chromecast
  light_icon: bool = False

  @property
  def cast_status(self) -> Optional[CastStatus]:
    pass

  @property
  def media_status(self) -> Optional[MediaStatus]:
    pass

  def can_play_next(self) -> Optional[bool]:
    pass

  def can_play_prev(self) -> Optional[bool]:
    pass

  def play_next(self):
    pass

  def play_prev(self):
    pass

  def open_uri(self, uri: str):
    pass

  def add_track(
    self,
    uri: str,
    after_track: DbusObj,
    set_as_current: bool
  ):
    pass


class StatusAttrsMixin(Wrapper):
  def __getattr__(self, name: str) -> Any:
    return getattr(self.cc, name)

  @property
  def cast_status(self) -> Optional[CastStatus]:
    if self.cc.status:
      return self.cc.status

    return None

  @property
  def media_status(self) -> Optional[MediaStatus]:
    if self.cc.media_controller.status:
      return self.cc.media_controller.status

    return None


class ControllersMixin(Wrapper):
  def __init__(self):
    self.yt_ctl, self.spotify_ctl, self.dash_ctl = ctls = [
      YouTubeController(),
      SpotifyController(),
      DashCastController(),
    ]

    for ctl in ctls:
      self._register(ctl)

    super().__init__()

  def _register(self, controller: BaseController):
    self.cc.register_handler(controller)

  def _launch_youtube(self):
    self.yt_ctl.launch()

  def _play_youtube(self, video_id: str):
    if not self.yt_ctl.is_active:
      self._launch_youtube()

    self.yt_ctl.play_video(video_id)

  def _get_url(self) -> Optional[str]:
    content_id = None

    if self.media_status:
      content_id = self.media_status.content_id

    if content_id and 'http' not in content_id and self.yt_ctl.is_active:
      return f"{YT_VID_URL}{content_id}"

    return content_id

  def open_uri(self, uri: str):
    video_id = get_video_id(uri)

    if video_id:
      self._play_youtube(video_id)
      return

    mimetype, _ = guess_type(uri)
    self.cc.media_controller.play_media(uri, mimetype)

  def add_track(
    self,
    uri: str,
    after_track: DbusObj,
    set_as_current: bool
  ):
    video_id = get_video_id(uri)

    if video_id:
      self.yt_ctl.add_to_queue(video_id)

    if video_id and set_as_current:
      self.yt_ctl.play_video(video_id)

    elif set_as_current:
      self.open_uri(uri)


class TitlesMixin(Wrapper):
  def get_stream_title(self) -> Optional[str]:
    title = self.cc.media_controller.title
    app_name = self.cc.app_display_name
    subtitle = self.get_subtitle()

    return title or app_name or subtitle

  def get_subtitle(self) -> Optional[str]:
    if not self.media_status:
      return None

    metadata = self.media_status.media_metadata

    if metadata and 'subtitle' in metadata:
      return metadata['subtitle']

    return None

  def get_artist(self, title: Optional[str] = None) -> Optional[str]:
    if not title:
      title = self.get_stream_title()

    subtitle = self.get_subtitle()

    artist: Optional[str] = None

    if not self.media_status:
      artist = self.media_status.artist

    app_name: Optional[str] = self.cc.app_display_name

    if artist:
      return artist

    elif subtitle:
      return subtitle

    elif app_name and app_name != title:
      return app_name

    return None

  def get_album(
    self,
    title: Optional[str] = None,
    artist: Optional[str] = None
  ) -> Optional[str]:
    if not title:
      title = self.get_stream_title()

    if not artist:
      artist = self.get_artist()

    album: Optional[str] = None

    if not self.media_status:
      album = self.media_status.album_name

    app_name = self.cc.app_display_name
    subtitle = self.get_subtitle()
    titles = {artist, title}

    if album:
      return album

    elif subtitle and subtitle not in titles:
      return subtitle

    elif app_name and app_name not in titles:
      return app_name

    return None


class TimeMixin(Wrapper):
  def __init__(self,):
    self._longest_duration: float = NO_DURATION
    super().__init__()

  def get_duration(self) -> Microseconds:
    duration = None

    if self.media_status:
      duration = self.media_status.duration

    current = self.get_current_position()
    longest = self._longest_duration

    if duration:
      return duration * US_IN_SEC

    elif longest and longest > current:
        return longest

    elif current:
      self._longest_duration = current
      return current

    return NO_DURATION

  def get_current_position(self) -> Microseconds:
    status = self.media_status

    if not status:
      return BEGINNING

    position_secs = status.adjusted_current_time

    if position_secs:
      return int(position_secs * US_IN_SEC)

    return BEGINNING

  def on_new_status(self, *args, **kwargs):
    # super().on_new_status(*args, **kwargs)
    status = self.media_status

    if not status:
      return

    if not status.current_time or \
        round(status.current_time, RESOLUTION) <= NO_DURATION:
      self._longest_duration = NO_DURATION

  def seek(self, time: Microseconds):
    seconds = int(round(time / US_IN_SEC))
    self.cc.media_controller.seek(seconds)

  def get_rate(self) -> RateDecimal:
    if not self.media_status:
      return DEFAULT_RATE

    rate = self.media_status.playback_rate

    if rate:
      return rate

    return DEFAULT_RATE

  def set_rate(self, val: RateDecimal):
    pass


class IconsMixin(Wrapper):
  def get_art_url(self, track: Optional[int] = None) -> str:
    thumb = self.media_controller.thumbnail
    icon = None

    if self.cast_status:
      icon = self.cast_status.icon_url

    if thumb:
      return thumb

    elif icon:
      return icon

    elif self.light_icon:
      return str(LIGHT_THUMB)

    return str(DEFAULT_THUMB)

  def get_desktop_entry(self) -> str:
    path = \
      DESKTOP_FILE_LIGHT if self.light_icon else DESKTOP_FILE_DARK

    if not path:
      return NO_DESKTOP_FILE

    # mpris requires stripped suffix
    path = path.with_suffix('')

    return str(path)

  def set_icon(self, lighter: bool = False):
    self.light_icon = lighter


class ChromecastWrapper(
  StatusAttrsMixin,
  TitlesMixin,
  ControllersMixin,
  TimeMixin,
  IconsMixin,
):
  """
  A wrapper to make it easier to switch out backend implementations.

  Holds common logic for dealing with underlying Chromecast API.
  """

  def __init__(self, cc: Chromecast):
    self.cc = cc
    super().__init__()

  def __repr__(self) -> str:
    cls = type(self)
    cls_name = cls.__name__

    return f"<{cls_name} for {self.cc}>"

  @property
  def name(self) -> str:
    return self.cc.name or DEFAULT_NAME

  def can_play_next(self) -> Optional[bool]:
    if self.media_status:
      return self.media_status.supports_queue_next

    return False

  def can_play_prev(self) -> Optional[bool]:
    if self.media_status:
      return self.media_status.supports_queue_prev

    return False

  def play_next(self):
    self.cc.media_controller.queue_next()

  def play_prev(self):
    self.cc.media_controller.queue_prev()

  def can_pause(self) -> Optional[bool]:
    return self.media_status.supports_pause

  def can_seek(self) -> Optional[bool]:
    return self.media_status.supports_seek

  def quit(self):
    self.cc.quit_app()

  def next(self):
    self.play_next()

  def previous(self):
    self.play_prev()

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

  def is_repeating(self) -> bool:
    return False

  def is_playlist(self) -> bool:
    return self.can_go_next() or self.can_go_previous()

  def set_repeating(self, val: bool):
    pass

  def set_loop_status(self, val: str):
    pass

  def get_shuffle(self) -> bool:
    return False

  def set_shuffle(self, val: bool):
    return False

  def get_volume(self) -> VolumeDecimal:
    if not self.cast_status:
      return None

    return self.cast_status.volume_level

  def set_volume(self, val: VolumeDecimal):
    curr = self.get_volume()
    diff = val - curr

    # can't adjust vol by 0
    if diff > NO_DELTA:  # vol up
      self.cc.volume_up(diff)

    elif diff < NO_DELTA:
      self.cc.volume_down(abs(diff))

  def is_mute(self) -> Optional[bool]:
    if self.cast_status:
      return self.cast_status.volume_muted

    return False

  def set_mute(self, val: bool):
    self.cc.set_volume_muted(val)

  def metadata(self) -> Metadata:
    title: Optional[str] = self.get_stream_title()
    artist = self.get_artist()
    artists = [artist] if artist else []
    dbus_name: DbusObj = get_track_id(title)
    comments: List[str] = []

    metadata = {
      "mpris:trackid": dbus_name,
      "mpris:length": self.get_duration(),
      "mpris:artUrl": self.get_art_url(),
      "xesam:url": self._get_url(),
      "xesam:title": title,
      "xesam:artist": artists,
      "xesam:album": self.get_album(title, artist),
      "xesam:albumArtist": artists,
      "xesam:discNumber": DEFAULT_DISC_NO,
      "xesam:trackNumber": self.media_status.track,
      "xesam:comment": comments,
    }

    return metadata

  def get_current_track(self) -> Track:
    title = self.get_stream_title()
    artist_name = self.get_artist()
    artist = Artist(artist_name)
    art_url = self.get_art_url()
    content_id = self._get_url()
    duration = int(self.get_duration())

    album = Album(
      name=self.get_album(title, artist_name),
      artists=(artist,),
      art_url=art_url,
    )

    track = Track(
      track_id=get_track_id(title),
      name=title,
      track_no=self.media_status.track,
      length=duration,
      uri=content_id,
      artists=(artist,),
      album=album,
      art_url=art_url,
      disc_no=DEFAULT_DISC_NO,
      type=get_media_type(self)
    )

    return track


@enforce_dbus_length
def get_track_id(name: str) -> DbusObj:
  return f"/track/{get_dbus_name(name)}"


def get_media_type(cc: ChromecastWrapper) -> Optional[ChromecastMediaType]:
  status = cc.media_status

  if not status:
    return None

  if status.media_is_movie:
    return ChromecastMediaType.MOVIE

  elif status.media_is_tvshow:
    return ChromecastMediaType.TVSHOW

  elif status.media_is_photo:
    return ChromecastMediaType.PHOTO

  elif status.media_is_musictrack:
    return ChromecastMediaType.MUSICTRACK

  elif status.media_is_generic:
    return ChromecastMediaType.GENERIC

  return None


def is_youtube(uri: str) -> bool:
  uri = uri.lower()
  return any(yt in uri for yt in YOUTUBE_URLS)


def get_video_id(uri: str) -> Optional[str]:
  video_id: Optional[str] = None

  if YT_LONG in uri:
    *_, video_id = uri.split('v=')

  elif YT_SHORT in uri:
    *_, video_id = uri.split('/')

  if video_id and '&' in video_id:
    video_id, *_ = video_id.split('&')

  return video_id
