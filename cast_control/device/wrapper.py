from __future__ import annotations

import logging
from abc import abstractmethod
from decimal import Decimal
from enum import StrEnum
from mimetypes import guess_type
from typing import Any, Final, NamedTuple, Protocol, Self, override
from urllib.parse import ParseResult, parse_qs, urlparse

from mpris_server import (
  BEGINNING, DEFAULT_RATE, DbusObj, MetadataObj, Microseconds, Paths, PlayState, Rate,
  ValidMetadata, Volume, get_track_id,
)
from pychromecast.controllers.bbciplayer import BbcIplayerController
from pychromecast.controllers.bbcsounds import BbcSoundsController
from pychromecast.controllers.bubbleupnp import BubbleUPNPController
from pychromecast.controllers.dashcast import DashCastController
from pychromecast.controllers.homeassistant_media import HomeAssistantMediaController
from pychromecast.controllers.media import BaseController, DefaultMediaReceiverController, MediaController, MediaStatus
from pychromecast.controllers.multizone import MultizoneController
from pychromecast.controllers.plex import PlexController
from pychromecast.controllers.receiver import CastStatus, ReceiverController
from pychromecast.controllers.supla import SuplaController
from pychromecast.controllers.yleareena import YleAreenaController
from pychromecast.controllers.youtube import YouTubeController
from pychromecast.socket_client import ConnectionStatus

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
PROTO: Final[str] = 'https'


class YoutubeUrl(StrEnum):
  long: Self = 'youtube.com'
  short: Self = 'youtu.be'

  watch_endpoint: Self = 'watch'
  playlist_endpoint: Self = 'playlist'

  video_qs: Self = 'v'
  playlist_qs: Self = 'list'

  video: Self = f'{PROTO}://{long}/{watch_endpoint}?{video_qs}='
  playlist: Self = f'{PROTO}://{long}/{playlist_endpoint}?{playlist_qs}='

  @classmethod
  def get_url(cls: type[Self], content_id: str | None, playlist_id: str | None = None) -> str | None:
    if content_id:
      return f"{cls.video}{content_id}"

    elif playlist_id:
      return f"{cls.playlist}{playlist_id}"

  @classmethod
  def is_youtube(cls: type[Self], uri: str | None) -> bool:
    if not uri:
      return False

    uri = uri.casefold()

    return get_domain(uri) in cls

  @classmethod
  def type(cls: type[Self], uri: str | None) -> Self | None:
    if not cls.which(uri):
      return None

    if cls.watch_endpoint in uri:
      return cls.video

    elif cls.playlist_endpoint in uri:
      return cls.playlist

    return cls.short

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
  app_id: str
  title: str


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

  @override
  def __getattr__(self, name: str) -> Any:
    return getattr(self.device, name)

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
    self.controllers.youtube.launch()

  def _play_youtube(self, video_id: str):
    youtube = self.controllers.youtube

    if not youtube.is_active:
      self._launch_youtube()

    youtube.quick_play(video_id)

  def _is_youtube_video(self, content_id: str | None) -> bool:
    if not content_id or not self.controllers.youtube.is_active:
      return False

    return not content_id.startswith('http')

  def _get_url(self) -> str | None:
    content_id: str | None = None

    if status := self.media_status:
      content_id = status.content_id

    if self._is_youtube_video(content_id):
      return YoutubeUrl.get_url(content_id)

    return content_id

  def open_uri(self, uri: str):
    if video_id := get_content_id(uri):
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
    youtube = self.controllers.youtube

    if video_id := get_content_id(uri):
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

    if (status := self.media_status) and (series_title := status.series_title):
      titles.append(series_title)

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
  _longest_duration: Microseconds | None = NO_DURATION

  def __init__(self):
    self._longest_duration = NO_DURATION
    super().__init__()

  @property
  def current_time(self) -> Seconds | None:
    if not (status := self.media_status):
      return None

    if time := status.adjusted_current_time or status.current_time:
      return Seconds(time)

    return None

  @override
  def on_new_status(self, *args, **kwargs):
    if not self.has_current_time():
      self._longest_duration = None

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
    position: Seconds = self.current_time

    if not position:
      return BEGINNING

    position_us: Microseconds = position * US_IN_SEC
    return round(position_us)

  def has_current_time(self) -> bool:
    current_time: Seconds | int = self.current_time

    if current_time is None:
      return False

    current_time = round(current_time, RESOLUTION)

    return current_time > BEGINNING

  def seek(self, time: Microseconds):
    time = Decimal(time)
    seconds = round(time / US_IN_SEC)

    self.media_controller.seek(seconds)

  def get_rate(self) -> Rate:
    if not (status := self.media_status):
      return DEFAULT_RATE

    if rate := status.playback_rate:
      return rate

    return DEFAULT_RATE

  def set_rate(self, val: Rate):
    pass


class IconsMixin(Wrapper):
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

    if images := self.media_status.images:
      first, *_ = images
      url, *_ = first

      self._set_cached_icon(url)
      return url

    if (status := self.cast_status) and (url := status.icon_url):
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
      disc_number=DEFAULT_DISC_NO,
      track_number=track_no,
      comments=comments,
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

  def set_repeating(self, val: bool):
    pass

  def set_loop_status(self, val: str):
    pass


class VolumeMixin(Wrapper):
  def get_volume(self) -> Volume | None:
    if status := self.cast_status:
      return Volume(status.volume_level)

    return None

  def set_volume(self, val: Volume):
    val = Volume(val)
    curr = self.get_volume()

    if curr is None:
      return

    delta: float = float(val - curr)

    # can't adjust vol by 0
    if delta > NO_DELTA:  # vol up
      self.device.volume_up(delta)

    elif delta < NO_DELTA:
      self.device.volume_down(abs(delta))

  def is_mute(self) -> bool | None:
    if status := self.cast_status:
      return status.volume_muted

    return False

  def set_mute(self, val: bool):
    self.device.set_volume_muted(val)


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


def get_media_type(
  dev: DeviceWrapper
) -> MediaType | None:
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


def get_domain(uri: str | ParseResult) -> str | None:
  match uri:
    case str():
      uri = urlparse(uri)

  *_, name, tld = uri.netloc.split(".")

  return f"{name}.{tld}"


def get_content_id(uri: str) -> str | None:
  if not YoutubeUrl.is_youtube(uri):
    return None

  parsed = urlparse(uri)
  content_id: str | None = None

  match get_domain(parsed), YoutubeUrl.type(uri):
    case YoutubeUrl.long, YoutubeUrl.video:
      qs = parse_qs(parsed.query)
      [content_id] = qs[YoutubeUrl.video_qs]

    case YoutubeUrl.long, YoutubeUrl.playlist:
      qs = parse_qs(parsed.query)
      [content_id] = qs[YoutubeUrl.playlist_qs]

    case YoutubeUrl.short, YoutubeUrl.video | YoutubeUrl.playlist:
      content_id = parsed.path[SKIP_FIRST]

  return content_id
