from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from enum import StrEnum
from mimetypes import guess_type
from typing import Any, Final, NamedTuple, Protocol, Self, override
from urllib.parse import ParseResult, parse_qs, urlparse

from mpris_server import (
  BEGINNING, DEFAULT_RATE, DbusObj, MetadataObj, Microseconds, Paths, PlayState, Rate,
  ValidMetadata, Volume, get_track_id, Track, Artist, Album
)
from pychromecast.controllers.bbciplayer import BbcIplayerController
from pychromecast.controllers.bbcsounds import BbcSoundsController
from pychromecast.controllers.bubbleupnp import BubbleUPNPController
from pychromecast.controllers.dashcast import DashCastController
from pychromecast.controllers.homeassistant_media import HomeAssistantMediaController
from pychromecast.controllers.media import BaseController, DefaultMediaReceiverController, MediaController, MediaImage, \
  MediaStatus
from pychromecast.controllers.multizone import MultizoneController
from pychromecast.controllers.plex import PlexController
from pychromecast.controllers.receiver import CastStatus, ReceiverController
from pychromecast.controllers.supla import SuplaController
from pychromecast.controllers.yleareena import YleAreenaController
from pychromecast.controllers.youtube import YouTubeController
from pychromecast.socket_client import ConnectionStatus
from validators import url

from .. import TITLE
from ..app.state import create_desktop_file, ensure_user_dirs_exist
from ..base import DEFAULT_DISC_NO, DEFAULT_ICON, DEFAULT_THUMB, Device, \
  LIGHT_THUMB, MediaType, NAME, NO_DELTA, NO_DESKTOP_FILE, \
  NO_DURATION, Seconds, US_IN_SEC, singleton


log: Final[logging.Logger] = logging.getLogger(__name__)


RESOLUTION: Final[int] = 1
MAX_TITLES: Final[int] = 3

NO_ARTIST: Final[str] = ''
NO_SUFFIX: Final[str] = ''

SKIP_FIRST: Final[slice] = slice(1, None)

PREFIX_NOT_YOUTUBE: Final[str] = 'http'
URL_PROTO: Final[str] = 'https'


class YoutubeUrl(StrEnum):
  long: Self = 'youtube.com'
  short: Self = 'youtu.be'

  watch_endpoint: Self = 'watch'
  playlist_endpoint: Self = 'playlist'

  video_query: Self = 'v'
  playlist_query: Self = 'list'

  video: Self = f'{URL_PROTO}://{long}/{watch_endpoint}?{video_query}='
  playlist: Self = f'{URL_PROTO}://{long}/{playlist_endpoint}?{playlist_query}='

  @classmethod
  def get_content_id(cls: type[Self], uri: str | None) -> str | None:
    return get_content_id(uri)

  @classmethod
  def get_url(cls: type[Self], video_id: str | None = None, playlist_id: str | None = None) -> str | None:
    if video_id:
      return f"{cls.video}{video_id}"

    elif playlist_id:
      return f"{cls.playlist}{playlist_id}"

    return None

  @classmethod
  def is_youtube(cls: type[Self], uri: str | None) -> bool:
    if not uri:
      return False

    uri = uri.casefold()

    return get_domain(uri) in cls

  @classmethod
  def type(cls: type[Self], uri: str | None) -> Self | None:
    if not (which := cls.which(uri)):
      return None

    if cls.watch_endpoint in uri:
      return cls.video

    elif cls.playlist_endpoint in uri:
      return cls.playlist

    return which

  @classmethod
  def which(cls: type[Self], uri: str | None) -> Self | None:
    if not cls.is_youtube(uri):
      return None

    if cls.long in uri:
      return cls.long

    elif cls.short in uri:
      return cls.short

    return None


class CachedIcon(NamedTuple):
  url: str
  app_id: str | None = None
  title: str | None = None


class Titles(NamedTuple):
  title: str | None = None
  artist: str | None = None
  album: str | None = None


class Controllers(NamedTuple):
  bbc_ip: BbcIplayerController | None = None
  bbc_sound: BbcSoundsController | None = None
  bubble: BubbleUPNPController | None = None
  dash: DashCastController | None = None
  default: DefaultMediaReceiverController | None = None
  ha_media: HomeAssistantMediaController | None = None
  multizone: MultizoneController | None = None
  plex: PlexController | None = None
  receiver: ReceiverController | None = None
  supla: SuplaController | None = None
  yle: YleAreenaController | None = None
  youtube: YouTubeController | None = None

  # plex_api: PlexApiController = None
  # ha: HomeAssistantController = None

  @classmethod
  def new(cls: type[Self], device: Device | None) -> Self:
    return cls(
      BbcIplayerController(),
      BbcSoundsController(),
      BubbleUPNPController(),
      DashCastController(),
      DefaultMediaReceiverController(),
      HomeAssistantMediaController(),
      MultizoneController(device.uuid) if device else None,
      PlexController(),
      ReceiverController(),
      SuplaController(),
      YleAreenaController(),
      YouTubeController(),
      # HomeAssistantController(),
    )


class ListenerIntegration(Protocol):
  @abstractmethod
  def on_new_status(self, *args, **kwargs):
    """Callback for event listener"""
    pass


class Wrapper(ListenerIntegration, Protocol):
  device: Device
  controllers: Controllers

  cached_icon: CachedIcon | None = None
  light_icon: bool = DEFAULT_ICON

  @property
  def name(self) -> str:
    return self.device.name or NAME

  @property
  @abstractmethod
  def cast_status(self) -> CastStatus | None:
    pass

  @property
  @abstractmethod
  def media_status(self) -> MediaStatus | None:
    pass

  @property
  @abstractmethod
  def connection_status(self) -> ConnectionStatus | None:
    pass

  @property
  @abstractmethod
  def media_controller(self) -> MediaController:
    pass

  @property
  @abstractmethod
  def titles(self) -> Titles:
    pass


class StatusMixin(Wrapper):
  @override
  @property
  def cast_status(self) -> CastStatus | None:
    return self.device.status or None

  @override
  @property
  def media_status(self) -> MediaStatus | None:
    return self.media_controller.status or None

  @override
  @property
  def connection_status(self) -> ConnectionStatus | None:
    return self.device.socket_client.receiver_controller.status or None

  @override
  @property
  def media_controller(self) -> MediaController:
    return self.device.media_controller


class ControllersMixin(Wrapper):
  controllers: Controllers

  def __init__(self):
    self._setup_controllers()
    super().__init__()

  def _setup_controllers(self):
    self.controllers = Controllers.new(self.device)

    for controller in self.controllers:
      if controller:
        self._register(controller)

  def _register(self, controller: BaseController):
    self.device.register_handler(controller)

  def _launch_youtube(self):
    if not (youtube := self.controllers.youtube):
      return

    youtube.launch()

  def _play_youtube(self, video_id: str):
    if not (youtube := self.controllers.youtube):
      return

    if not youtube.is_active:
      self._launch_youtube()

    youtube.quick_play(video_id)

  def _is_youtube_video(self, content_id: str | None) -> bool:
    if not (youtube := self.controllers.youtube):
      return False

    if not content_id or not youtube.is_active:
      return False

    return not content_id.startswith(PREFIX_NOT_YOUTUBE)

  def _get_url(self) -> str | None:
    content_id: str | None = None

    if status := self.media_status:
      content_id = status.content_id

    if self._is_youtube_video(content_id):
      return YoutubeUrl.get_url(content_id)

    return content_id

  def open_uri(self, uri: str):
    if video_id := YoutubeUrl.get_content_id(uri):
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
    if not (youtube := self.controllers.youtube):
      self.open_uri(uri)
      return

    if video_id := YoutubeUrl.get_content_id(uri):
      youtube.add_to_queue(video_id)

    if video_id and set_as_current:
      youtube.play_video(video_id)

    elif set_as_current:
      self.open_uri(uri)


class TitlesMixin(Wrapper):
  @override
  @property
  def titles(self) -> Titles:
    titles: list[str] = list()

    if title := self.media_controller.title:
      titles.append(title)

    if (status := self.media_status) and (title := status.series_title):
      titles.append(title)

    if subtitle := self.get_subtitle():
      titles.append(subtitle)

    if status:
      if artist := status.artist:
        titles.append(artist)

      if album := status.album_name:
        titles.append(album)

    if app_name := self.device.app_display_name:
      titles.append(app_name)

    if not titles:
      titles.append(TITLE)

    titles = titles[:MAX_TITLES]

    return Titles(*titles)

  def get_subtitle(self) -> str | None:
    if not (status := self.media_status) or not (metadata := status.media_metadata):
      return None

    if subtitle := metadata.get('subtitle'):
      return subtitle

    return None


class TimeMixin(Wrapper):
  _longest_duration: Microseconds | None

  def __init__(self):
    self._longest_duration = NO_DURATION
    super().__init__()

  def _reset_longest_duration(self):
    if not self.has_current_time():
      self._longest_duration = None

  @property
  def current_time(self) -> Seconds | None:
    if not (status := self.media_status):
      return None

    if time := status.adjusted_current_time or status.current_time:
      return Seconds(time)

    return None

  @override
  def on_new_status(self, *args, **kwargs):
    self._reset_longest_duration()
    super().on_new_status(*args, **kwargs)

  def get_duration(self) -> Microseconds:
    if (status := self.media_status) and (duration := status.duration) is not None:
      duration = Seconds(duration)
      duration_us: Microseconds = duration * US_IN_SEC

      return round(duration_us)

    current: Microseconds = self.get_current_position()
    longest: Microseconds = self._longest_duration

    if longest and longest > current:
      return longest

    elif current:
      self._longest_duration = current
      return current

    return NO_DURATION

  def get_current_position(self) -> Microseconds:
    position: Seconds | None = self.current_time

    if not position:
      return BEGINNING

    position_us: Microseconds = position * US_IN_SEC
    return round(position_us)

  def has_current_time(self) -> bool:
    current_time: Seconds | None = self.current_time

    if current_time is None:
      return False

    current_time = round(current_time, RESOLUTION)

    return current_time > BEGINNING

  def seek(self, time: Microseconds):
    microseconds = Decimal(time)
    seconds: int = round(microseconds / US_IN_SEC)

    self.media_controller.seek(seconds)

  def get_rate(self) -> Rate:
    if not (status := self.media_status):
      return DEFAULT_RATE

    if rate := status.playback_rate:
      return rate

    return DEFAULT_RATE

  def set_rate(self, value: Rate):
    pass


class IconsMixin(Wrapper):
  cached_icon: CachedIcon | None
  light_icon: bool

  def _set_cached_icon(self, url: str | None = None):
    if not url:
      self.cached_icon = None
      return

    app_id = self.device.app_id
    title, *_ = self.titles
    self.cached_icon = CachedIcon(url, app_id, title)

  def _can_use_cache(self) -> bool:
    if not (icon := self.cached_icon) or not icon.url:
      return False

    app_id = self.device.app_id
    title, *_ = self.titles

    return icon.app_id == app_id and icon.title == title

  def _get_icon_from_device(self) -> str | None:
    url: str | None

    if (status := self.media_status) and (images := status.images):
      first: MediaImage

      first, *_ = images
      url, *_ = first
      self._set_cached_icon(url)

      return url

    if (status := self.cast_status) and (url := status.icon_url):
      self._set_cached_icon(url)
      return url

    if not self._can_use_cache():
      return None

    if icon := self.cached_icon:
      return icon.url

    return None

  @ensure_user_dirs_exist
  def _get_default_icon(self) -> str:
    if self.light_icon:
      return str(LIGHT_THUMB)

    return str(DEFAULT_THUMB)

  def get_art_url(self, track: int | None = None) -> str:
    if icon := self._get_icon_from_device():
      return icon

    return self._get_default_icon()

  @singleton
  def get_desktop_entry(self) -> Paths:
    try:
      return create_desktop_file(self.light_icon)

    except Exception as e:
      log.exception(e)
      log.error("Couldn't load desktop file.")

      return NO_DESKTOP_FILE

  def set_icon(self, lighter: bool = False):
    self.light_icon: bool = lighter


class MetadataMixin(Wrapper):
  def metadata(self) -> ValidMetadata:
    title, artist, album = self.titles

    dbus_name: DbusObj = get_track_id(title)
    artists: list[str] = [artist] if artist else []
    comments: list[str] = []
    track_no: int | None = None

    if status := self.media_status:
      track_no = status.track

    return MetadataObj(
      album=album,
      album_artists=artists,
      art_url=self.get_art_url(),
      artists=artists,
      comments=comments,
      disc_number=DEFAULT_DISC_NO,
      length=self.get_duration(),
      title=title,
      track_id=dbus_name,
      track_number=track_no,
      url=self._get_url(),
    )

  def get_stream_title(self) -> str:
    if status := self.media_status:
      return status.title

    return self.titles.title

  def get_current_track(self) -> Track:
    title, artist, album = self.titles

    dbus_name: DbusObj = get_track_id(title)
    artists: list[str] = [Artist(artist)] if artist else []
    track_no: int | None = None
    art_url = self.get_art_url()

    if status := self.media_status:
      track_no = status.track

    return Track(
      album=Album(art_url, artists, album),
      art_url=art_url,
      artists=artists,
      disc_no=DEFAULT_DISC_NO,
      length=self.get_duration(),
      name=title,
      track_id=dbus_name,
      track_no=track_no,
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

  def set_shuffle(self, value: bool):
    pass

  def play_next(self):
    self.media_controller.queue_next()

  def play_prev(self):
    self.media_controller.queue_prev()

  def quit(self):
    self.device.quit_app()

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

  def set_repeating(self, value: bool):
    pass

  def set_loop_status(self, value: str):
    pass


class VolumeMixin(Wrapper):
  def get_volume(self) -> Volume | None:
    if status := self.cast_status:
      return Volume(status.volume_level)

    return None

  def set_volume(self, value: Volume):
    if (current := self.get_volume()) is None:
      return

    volume = Volume(value)
    delta: float = float(volume - current)

    # can't adjust vol by 0
    if delta > NO_DELTA:  # vol up
      self.device.volume_up(delta)

    elif delta < NO_DELTA:
      self.device.volume_down(abs(delta))

  def is_mute(self) -> bool | None:
    if status := self.cast_status or self.media_status:
      return status.volume_muted

    return False

  def set_mute(self, value: bool):
    self.device.set_volume_muted(value)


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
    if status := self.media_status:
      return status.supports_queue_next

    return False

  def can_play_prev(self) -> bool:
    if status := self.media_status:
      return status.supports_queue_prev

    return False

  def can_pause(self) -> bool:
    if status := self.media_status:
      return status.supports_pause

    return False

  def can_seek(self) -> bool:
    if status := self.media_status:
      return status.supports_seek

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
  """Wraps implementation details for device API"""

  def __init__(self, device: Device):
    self.device = device
    super().__init__()

  def __repr__(self) -> str:
    cls = type(self)
    cls_name = cls.__name__

    return f'<{cls_name} for {self.device}>'


class BaseDeviceWrapper(ABC):
  @abstractmethod
  def add_track(
    self,
    uri: str,
    after_track: DbusObj,
    set_as_current: bool
  ):
    pass

  @abstractmethod
  def can_control(self) -> bool:
    pass

  @abstractmethod
  def can_edit_track(self) -> bool:
    pass

  @abstractmethod
  def can_pause(self) -> bool:
    pass

  @abstractmethod
  def can_play(self) -> bool:
    pass

  @abstractmethod
  def can_play_next(self) -> bool:
    pass

  @abstractmethod
  def can_play_prev(self) -> bool:
    pass

  @abstractmethod
  def can_quit(self) -> bool:
    pass

  @abstractmethod
  def can_seek(self) -> bool:
    pass

  @abstractmethod
  def get_art_url(self, track: int | None = None) -> str:
    pass

  @abstractmethod
  def get_desktop_entry(self) -> Paths:
    pass

  @abstractmethod
  def get_duration(self) -> Microseconds:
    pass

  @abstractmethod
  def get_playstate(self) -> PlayState:
    pass

  @abstractmethod
  def get_rate(self) -> Rate:
    pass

  @abstractmethod
  def get_shuffle(self) -> bool:
    pass

  @abstractmethod
  def get_stream_title(self) -> str:
    pass

  @abstractmethod
  def get_volume(self) -> Volume | None:
    pass

  @abstractmethod
  def has_current_time(self) -> bool:
    pass

  @abstractmethod
  def is_mute(self) -> bool | None:
    pass

  @abstractmethod
  def is_playlist(self) -> bool:
    pass

  @abstractmethod
  def is_repeating(self) -> bool:
    pass

  @abstractmethod
  def metadata(self) -> ValidMetadata:
    pass

  @abstractmethod
  def next(self):
    pass

  @abstractmethod
  def open_uri(self, uri: str):
    pass

  @abstractmethod
  def pause(self):
    pass

  @abstractmethod
  def play(self):
    pass

  @abstractmethod
  def play_next(self):
    pass

  @abstractmethod
  def play_prev(self):
    pass

  @abstractmethod
  def previous(self):
    pass

  @abstractmethod
  def quit(self):
    pass

  @abstractmethod
  def resume(self):
    pass

  @abstractmethod
  def seek(
    self,
    time: Microseconds,
    track_id: DbusObj | None = None
  ):
    pass

  @abstractmethod
  def set_icon(self, lighter: bool = False):
    pass

  @abstractmethod
  def set_loop_status(self, value: str):
    pass

  @abstractmethod
  def set_mute(self, value: bool):
    pass

  @abstractmethod
  def set_rate(self, value: Rate):
    pass

  @abstractmethod
  def set_repeating(self, value: bool):
    pass

  @abstractmethod
  def set_shuffle(self, value: bool):
    pass

  @abstractmethod
  def set_volume(self, value: Volume):
    pass

  @abstractmethod
  def stop(self):
    pass

  @abstractmethod
  def titles(self) -> Titles:
    pass


def get_media_type(device_wrapper: DeviceWrapper) -> MediaType | None:
  if not (status := device_wrapper.media_status):
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


def get_domain(uri: str | ParseResult) -> str | None:
  if not url(uri):
    return None

  if isinstance(uri, str):
    uri = urlparse(uri)

  *_, name, tld = uri.netloc.split(".")

  return f"{name}.{tld}"


def get_content_id(uri: str) -> str | None:
  if not url(uri) or not YoutubeUrl.is_youtube(uri):
    return None

  parsed = urlparse(uri)
  content_id: str | None = None

  match get_domain(parsed), YoutubeUrl.type(uri):
    case YoutubeUrl.long, YoutubeUrl.video:
      qs = parse_qs(parsed.query)
      [content_id] = qs[YoutubeUrl.video_query]

    case YoutubeUrl.long, YoutubeUrl.playlist:
      qs = parse_qs(parsed.query)
      [content_id] = qs[YoutubeUrl.playlist_query]

    case YoutubeUrl.short, YoutubeUrl.video | YoutubeUrl.playlist:
      content_id = parsed.path[SKIP_FIRST]

  return content_id
