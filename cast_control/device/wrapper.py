from __future__ import annotations
from typing import Optional, Any, Union, \
  NamedTuple, Callable
from pathlib import Path
from mimetypes import guess_type
from functools import lru_cache
import logging

from pychromecast.controllers.receiver import CastStatus
from pychromecast.controllers.media import MediaStatus, \
  BaseController, MediaController
from pychromecast.controllers.youtube import YouTubeController
from pychromecast.controllers.spotify import SpotifyController
from pychromecast.controllers.dashcast import DashCastController
from pychromecast.controllers.bbciplayer import BbcIplayerController
from pychromecast.controllers.bbcsounds import BbcSoundsController
from pychromecast.controllers.bubbleupnp import BubbleUPNPController
from pychromecast.controllers.supla import SuplaController
from pychromecast.controllers.yleareena import YleAreenaController
from pychromecast.controllers.homeassistant import HomeAssistantController
from pychromecast.controllers.plex import PlexApiController
from pychromecast.controllers.plex import PlexController

from mpris_server.adapters import PlayState, Microseconds, \
  VolumeDecimal, RateDecimal, Paths
from mpris_server.base import BEGINNING, DEFAULT_RATE, DbusObj
from mpris_server.mpris.compat import get_track_id
from mpris_server.mpris.metadata import Metadata, MetadataObj, ValidMetadata

from .. import TITLE
from ..types import Protocol, runtime_checkable, Final
from ..base import DEFAULT_THUMB, LIGHT_THUMB, NO_DURATION, NO_DELTA, \
  US_IN_SEC, DEFAULT_DISC_NO, MediaType, NO_DESKTOP_FILE, LRU_MAX_SIZE, \
  NAME, DEFAULT_ICON, Device
from ..app.state import create_desktop_file, ensure_user_dirs_exist, \
  create_user_dirs


RESOLUTION: Final[int] = 1
MAX_TITLES: Final[int] = 3

YOUTUBE_URLS: Final[set[str]] = {
  'youtube.com/',
  'youtu.be/'
}
YT_LONG, YT_SHORT = YOUTUBE_URLS
YT_VID_URL: Final[str] = f'https://{YT_LONG}watch?v='

NO_ARTIST: Final[str] = ''
NO_SUFFIX: Final[str] = ''


class CachedIcon(NamedTuple):
  url: str
  app_id: str
  title: str


class Titles(NamedTuple):
  title: Optional[str] = None
  artist: Optional[str] = None
  album: Optional[str] = None


class Controllers(NamedTuple):
  yt: YouTubeController
  spotify: Optional[SpotifyController] = None
  dash: Optional[DashCastController] = None
  plex: Optional[PlexController] = None
  supla: Optional[SuplaController] = None
  # bbc_ip: BbcIplayerController = None
  # bbc_sound: BbcSoundsController = None
  # bubble: BubbleUPNPController = None
  # yle: YleAreenaController = None
  # plex_api: PlexApiController = None
  # ha: HomeAssistantController = None


@runtime_checkable
class Wrapper(Protocol):
  dev: Device
  ctls: Controllers
  cached_icon: Optional[CachedIcon] = None
  light_icon: bool = DEFAULT_ICON

  def __getattr__(self, name: str) -> Any:
    return getattr(self.dev, name)

  @property
  def name(self) -> str:
    return self.dev.name or NAME

  @property
  def cast_status(self) -> Optional[CastStatus]:
    pass

  @property
  def media_status(self) -> Optional[MediaStatus]:
    pass

  @property
  def media_controller(self) -> MediaController:
    pass

  @property
  def titles(self) -> Titles:
    pass

  def on_new_status(self, *args, **kwargs):
    '''Callback for event listener'''
    pass


class StatusMixin(Wrapper):
  @property
  def cast_status(self) -> Optional[CastStatus]:
    if self.dev.status:
      return self.dev.status

    return None

  @property
  def media_status(self) -> Optional[MediaStatus]:
    if self.media_controller.status:
      return self.media_controller.status

    return None

  @property
  def media_controller(self) -> MediaController:
    return self.dev.media_controller


class ControllersMixin(Wrapper):
  def __init__(self):
    self._setup_controllers()
    super().__init__()

  def _setup_controllers(self):
    self.ctls = Controllers(
      YouTubeController(),
      SpotifyController(),
      DashCastController(),
      PlexController(),
      SuplaController(),
      # BbcIplayerController(),
      # BbcSoundsController(),
      # BubbleUPNPController(),
      # YleAreenaController(),
      # PlexApiController(),
      # HomeAssistantController(),
    )

    for ctl in self.ctls:
      if ctl:
        self._register(ctl)

  def _register(self, controller: BaseController):
    self.dev.register_handler(controller)

  def _launch_youtube(self):
    self.ctls.yt.launch()

  def _play_youtube(self, video_id: str):
    yt = self.ctls.yt

    if not yt.is_active:
      self._launch_youtube()

    yt.play_video(video_id)

  def _is_youtube_vid(self, content_id: str) -> bool:
    if not content_id or not self.ctls.yt.is_active:
      return False

    return not content_id.startswith('http')

  def _get_url(self) -> Optional[str]:
    content_id = None

    if self.media_status:
      content_id = self.media_status.content_id

    if self._is_youtube_vid(content_id):
      return f'{YT_VID_URL}{content_id}'

    return content_id

  def open_uri(self, uri: str):
    video_id = get_video_id(uri)

    if video_id:
      self._play_youtube(video_id)
      return

    mimetype, _ = guess_type(uri)
    self.media_controller.play_media(uri, mimetype)

  def add_track(
    self,
    uri: str,
    after_track: DbusObj,
    set_as_current: bool
  ):
    video_id = get_video_id(uri)
    yt = self.ctls.yt

    if video_id:
      yt.add_to_queue(video_id)

    if video_id and set_as_current:
      yt.play_video(video_id)

    elif set_as_current:
      self.open_uri(uri)


class TitlesMixin(Wrapper):
  @property
  def titles(self) -> Titles:
    titles: list[str] = list()

    title = self.media_controller.title

    if title:
      titles.append(title)

    if self.media_status:
      series_title = self.media_status.series_title

      if series_title:
        titles.append(series_title)

    subtitle = self.get_subtitle()

    if subtitle:
      titles.append(subtitle)

    if self.media_status:
      artist = self.media_status.artist

      if artist:
        titles.append(artist)

      album = self.media_status.album_name

      if album:
        titles.append(album)

    app_name = self.dev.app_display_name

    if app_name:
      titles.append(app_name)

    if not titles:
      titles.append(TITLE)

    titles = titles[:MAX_TITLES]

    return Titles(*titles)

  def get_subtitle(self) -> Optional[str]:
    if not self.media_status:
      return None

    metadata = self.media_status.media_metadata

    if metadata and 'subtitle' in metadata:
      return metadata['subtitle']

    return None


class TimeMixin(Wrapper):
  _longest_duration: float = NO_DURATION

  def __init__(self):
    self._longest_duration = NO_DURATION
    super().__init__()

  @property
  def current_time(self) -> Optional[float]:
    status = self.media_status

    if not status:
      return None

    return status.adjusted_current_time or status.current_time

  def get_duration(self) -> Microseconds:
    duration: Optional[float] = None

    if self.media_status:
      duration = self.media_status.duration

    if duration is not None:
      return duration * US_IN_SEC

    longest = self._longest_duration
    current = self.get_current_position()

    if longest and longest > current:
      return longest

    elif current:
      self._longest_duration = current
      return current

    return NO_DURATION

  def get_current_position(self) -> Microseconds:
    position_secs = self.current_time

    if not position_secs:
      return BEGINNING

    position_us = position_secs * US_IN_SEC
    return round(position_us)

  def on_new_status(self, *args, **kwargs):
    # super().on_new_status(*args, **kwargs)
    if not self.has_current_time():
      self._longest_duration = None

  def has_current_time(self) -> bool:
    current_time = self.current_time

    if current_time is None:
      return False

    current_time = round(current_time, RESOLUTION)

    return current_time > BEGINNING

  def seek(self, time: Microseconds):
    seconds = int(round(time / US_IN_SEC))
    self.media_controller.seek(seconds)

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
  def _set_cached_icon(self, url: Optional[str] = None):
    if not url:
      self.cached_icon = None
      return

    app_id = self.dev.app_id
    title, *_ = self.titles
    self.cached_icon = CachedIcon(url, app_id, title)

  def _can_use_cache(self) -> bool:
    cache = self.cached_icon

    if not cache or not cache.url:
      return False

    app_id = self.dev.app_id
    title, *_ = self.titles

    if cache.app_id != app_id or cache.title != title:
      return False

    return True

  def _get_icon_from_device(self) -> Optional[str]:
    images = self.media_status.images

    if images:
      first, *_ = images
      url, *_ = first

      self._set_cached_icon(url)
      return url

    url: Optional[str] = None

    if self.cast_status:
      url = self.cast_status.icon_url

    if url:
      self._set_cached_icon(url)
      return url

    if not self._can_use_cache():
      return None

    return self.cached_icon.url

  @ensure_user_dirs_exist
  def _get_default_icon(self) -> str:
    if self.light_icon:
      return str(LIGHT_THUMB)

    return str(DEFAULT_THUMB)

  def get_art_url(self, track: Optional[int] = None) -> str:
    icon = self._get_icon_from_device()

    if icon:
      return icon

    return self._get_default_icon()

  @lru_cache(LRU_MAX_SIZE)
  def get_desktop_entry(self) -> Paths:
    try:
      path = create_desktop_file(self.light_icon)

    except Exception as e:
      logging.exception(e)
      logging.error("Couldn't load desktop file.")
      return NO_DESKTOP_FILE

    return path

  def set_icon(self, lighter: bool = False):
    self.light_icon: bool = lighter


class MetadataMixin(Wrapper):
  def metadata(self) -> ValidMetadata:
    title, artist, album = self.titles

    artists = [artist] if artist else []
    dbus_name: DbusObj = get_track_id(title)
    comments: list[str] = []
    track_no: Optional[int] = None

    if self.media_status:
      track_no = self.media_status.track

    return MetadataObj(
      track_id=dbus_name,
      length=self.get_duration(),
      art_url=self.get_art_url(),
      url=self._get_url(),
      title=title,
      artists=artists,
      album=album,
      album_artists=artists,
      disc_no=DEFAULT_DISC_NO,
      track_no=track_no,
      comments=comments
    )


class PlaybackMixin(Wrapper):
  def get_playstate(self) -> PlayState:
    if self.media_controller.is_playing:
      return PlayState.PLAYING

    elif self.media_controller.is_paused:
      return PlayState.PAUSED

    return PlayState.STOPPED

  def is_repeating(self) -> bool:
    return False

  def is_playlist(self) -> bool:
    return self.can_go_next() or self.can_go_previous()

  def get_shuffle(self) -> bool:
    return False

  def set_shuffle(self, val: bool):
    return False

  def play_next(self):
    self.media_controller.queue_next()

  def play_prev(self):
    self.media_controller.queue_prev()

  def quit(self):
    self.dev.quit_app()

  def next(self):
    self.play_next()

  def previous(self):
    self.play_prev()

  def pause(self):
    self.media_controller.pause()

  def resume(self):
    self.play()

  def stop(self):
    self.media_controller.stop()

  def play(self):
    self.media_controller.play()

  def set_repeating(self, val: bool):
    pass

  def set_loop_status(self, val: str):
    pass


class VolumeMixin(Wrapper):
  def get_volume(self) -> Optional[VolumeDecimal]:
    if not self.cast_status:
      return None

    return self.cast_status.volume_level

  def set_volume(self, val: VolumeDecimal):
    curr = self.get_volume()

    if curr is None:
      return

    delta: float = val - curr

    # can't adjust vol by 0
    if delta > NO_DELTA:  # vol up
      self.dev.volume_up(delta)

    elif delta < NO_DELTA:
      self.dev.volume_down(abs(delta))

  def is_mute(self) -> Optional[bool]:
    if self.cast_status:
      return self.cast_status.volume_muted

    return False

  def set_mute(self, val: bool):
    self.dev.set_volume_muted(val)


class AbilitiesMixin(Wrapper):
  def can_quit(self) -> bool:
    return True

  def can_play(self) -> bool:
    state = self.get_playstate()

    return state is not PlayState.STOPPED

  def can_control(self) -> bool:
    return True
    # return self.can_play() or self.can_pause() \
    #   or self.can_play_next() or self.can_play_prev() \
    #   or self.can_seek()

  def can_edit_track(self) -> bool:
    return False

  def can_play_next(self) -> bool:
    if self.media_status:
      return self.media_status.supports_queue_next

    return False

  def can_play_prev(self) -> bool:
    if self.media_status:
      return self.media_status.supports_queue_prev

    return False

  def can_pause(self) -> bool:
    if self.media_status:
      return self.media_status.supports_pause

    return False

  def can_seek(self) -> bool:
    if self.media_status:
      return self.media_status.supports_seek

    return False


class DeviceWrapper(
  StatusMixin,
  TitlesMixin,
  ControllersMixin,
  TimeMixin,
  IconsMixin,
  MetadataMixin,
  PlaybackMixin,
  VolumeMixin,
  AbilitiesMixin,
):
  '''Wraps implementation details for device API'''

  def __init__(self, dev: Device):
    self.dev = dev
    super().__init__()

  def __repr__(self) -> str:
    cls = type(self)
    cls_name = cls.__name__

    return f'<{cls_name} for {self.dev}>'


def get_media_type(
  dev: DeviceWrapper
) -> Optional[MediaType]:
  status = dev.media_status

  if not status:
    return None

  if status.media_is_movie:
    return MediaType.MOVIE

  elif status.media_is_tvshow:
    return MediaType.TVSHOW

  elif status.media_is_photo:
    return MediaType.PHOTO

  elif status.media_is_musictrack:
    return MediaType.MUSICTRACK

  elif status.media_is_generic:
    return MediaType.GENERIC

  return None


def is_youtube(uri: str) -> bool:
  uri = uri.casefold()
  return any(yt in uri for yt in YOUTUBE_URLS)


def get_video_id(uri: str) -> Optional[str]:
  if not is_youtube(uri):
    return None

  video_id: Optional[str] = None

  if YT_LONG in uri:
    *_, video_id = uri.split('v=')

  elif YT_SHORT in uri:
    *_, video_id = uri.split('/')

  if video_id and '&' in video_id:
    video_id, *_ = video_id.split('&')

  return video_id
