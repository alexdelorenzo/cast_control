from __future__ import annotations

import logging
from decimal import Decimal
from mimetypes import guess_type
from typing import Final, override

from mpris_server import (
  Album, Artist, BEGINNING, DEFAULT_RATE, DbusObj, LoopStatus, MetadataObj, Microseconds, Paths, PlayState, Rate, Track,
  ValidMetadata, Volume, get_track_id,
)
from pychromecast.controllers.media import MediaController, MediaImage, MediaStatus
from pychromecast.controllers.receiver import CastStatus
from pychromecast.socket_client import ConnectionStatus

from .base import CachedIcon, Controllers, Titles, TitlesBuilder, YoutubeUrl
from .. import TITLE
from ..app.state import create_desktop_file, ensure_user_dirs_exist
from ..base import DEFAULT_DISC_NO, DEFAULT_THUMB, Device, \
  LIGHT_THUMB, NO_DELTA, NO_DESKTOP_FILE, \
  NO_DURATION, Seconds, US_IN_SEC, singleton
from ..protocols import CliIntegration, ListenerIntegration, ModuleIntegration, Wrapper


log: Final[logging.Logger] = logging.getLogger(__name__)


RESOLUTION: Final[int] = 1
MAX_TITLES: Final[int] = 3

NO_ARTIST: Final[str] = ''
NO_SUFFIX: Final[str] = ''

PREFIX_NOT_YOUTUBE: Final[str] = 'http'


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

  @override
  def __init__(self):
    self._setup_controllers()
    super().__init__()

  def _setup_controllers(self):
    self.controllers = Controllers.new(self.device)
    self.controllers.register(self.device)

  def _launch_youtube(self):
    if not (youtube := self.controllers.youtube):
      return

    youtube.launch()

  def _play_youtube(self, video_id: str):
    if not (youtube := self.controllers.youtube):
      return

    if not youtube.is_active:
      self._launch_youtube()

    youtube.quick_play(media_id=video_id, timeout=30)

  @property
  def is_youtube(self) -> bool:
    if youtube := self.controllers.youtube:
      return youtube.is_active

    return False

  @override
  def open_uri(self, uri: str):
    if content_id := YoutubeUrl.get_content_id(uri):
      self._play_youtube(content_id)
      return

    mimetype, _ = guess_type(uri)
    self.media_controller.play_media(uri, mimetype)

  @override
  def add_track(self, uri: str, after_track: DbusObj, set_as_current: bool):
    if not (youtube := self.controllers.youtube):
      self.open_uri(uri)
      return

    if content_id := YoutubeUrl.get_content_id(uri):
      youtube.add_to_queue(content_id)

    if content_id and set_as_current:
      youtube.play_video(content_id)

    elif set_as_current:
      self.open_uri(uri)


class TitlesMixin(Wrapper):
  @override
  @property
  def titles(self) -> Titles:
    titles: TitlesBuilder = TitlesBuilder()

    if title := self.media_status.title:
      titles.set(title=title)

    if (subtitle := self.get_subtitle()) and self.is_youtube:
      titles.set(artist=subtitle)

    elif subtitle:
      titles.add(subtitle)

    if status := self.media_status:
      if title := status.series_title:
        titles.set(title=title, overwrite=False)

      if artist := status.artist:
        titles.set(artist=artist)

      if album := status.album_name:
        titles.set(album=album)

    if app_name := self.device.app_display_name:
      if not titles.artist:
        titles.set(artist=app_name)

      elif not titles.album:
        titles.set(album=app_name)

      elif not titles.title:
        titles.set(title=app_name)

    titles.add(TITLE)

    return titles.build()

  def get_subtitle(self) -> str | None:
    if not (status := self.media_status) or not (metadata := status.media_metadata):
      return None

    if subtitle := metadata.get('subtitle'):
      return subtitle

    return None


class TimeMixin(Wrapper, ListenerIntegration, ModuleIntegration):
  _longest_duration: Microseconds | None

  @override
  def __init__(self):
    self._longest_duration = NO_DURATION
    super().__init__()

  def _reset_longest_duration(self):
    if not self.has_current_time():
      self._longest_duration = None

  @override
  def on_new_status(self, *args, **kwargs):
    self._reset_longest_duration()
    super().on_new_status(*args, **kwargs)

  @override
  @property
  def current_time(self) -> Seconds | None:
    if not (status := self.media_status):
      return None

    if time := status.adjusted_current_time or status.current_time:
      return Seconds(time)

    return None

  @override
  def get_duration(self) -> Microseconds:
    if (status := self.media_status) and (duration := status.duration) is not None:
      duration = Seconds(duration)
      duration_us = duration * US_IN_SEC

      return round(duration_us)

    current: Microseconds = self.get_current_position()
    longest: Microseconds = self._longest_duration

    if longest and longest > current:
      return longest

    elif current:
      self._longest_duration = current
      return current

    return NO_DURATION

  @override
  def get_current_position(self) -> Microseconds:
    position: Seconds | None = self.current_time

    if not position:
      return BEGINNING

    position_us = position * US_IN_SEC
    return round(position_us)

  @override
  def has_current_time(self) -> bool:
    current_time: Seconds | None = self.current_time

    if current_time is None:
      return False

    current_time = round(current_time, RESOLUTION)

    return current_time > BEGINNING

  @override
  def seek(self, time: Microseconds, *_):
    microseconds = Decimal(time)
    seconds: int = round(microseconds / US_IN_SEC)

    self.media_controller.seek(seconds)

  @override
  def get_rate(self) -> Rate:
    if not (status := self.media_status):
      return DEFAULT_RATE

    if rate := status.playback_rate:
      return rate

    return DEFAULT_RATE

  @override
  def set_rate(self, value: Rate):
    pass


class IconsMixin(Wrapper, CliIntegration):
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

  @override
  def get_art_url(self, track: int | None = None) -> str:
    if icon := self._get_icon_from_device():
      return icon

    return self._get_default_icon()

  @override
  @singleton
  def get_desktop_entry(self) -> Paths:
    try:
      return create_desktop_file(self.light_icon)

    except Exception as e:
      log.exception(e)
      log.error("Couldn't load desktop file.")

      return NO_DESKTOP_FILE

  @override
  def set_icon(self, lighter: bool = False):
    self.light_icon: bool = lighter


class MetadataMixin(Wrapper):
  def _get_url(self) -> str | None:
    content_id: str | None = None

    if status := self.media_status:
      content_id = status.content_id

    if self._is_youtube_video(content_id):
      return YoutubeUrl.get_url(content_id)

    return content_id

  def _is_youtube_video(self, content_id: str | None) -> bool:
    if not (youtube := self.controllers.youtube):
      return False

    if not content_id or not youtube.is_active:
      return False

    return not content_id.startswith(PREFIX_NOT_YOUTUBE)

  @override
  def metadata(self) -> ValidMetadata:
    title, artist, album, comments = self.titles

    dbus_name: DbusObj = get_track_id(title)
    artists: list[str] = [artist] if artist else []
    comments: list[str] = [comments] if comments else []
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

  @override
  def get_stream_title(self) -> str:
    if status := self.media_status:
      return status.title

    return self.titles.title

  @override
  def get_current_track(self) -> Track:
    title, artist, album, comments = self.titles

    dbus_name: DbusObj = get_track_id(title)
    artists: list[Artist] = [Artist(artist)] if artist else []
    track_no: int | None = None
    art_url = self.get_art_url()

    if status := self.media_status:
      track_no = status.track

    return Track(
      album=Album(art_url, artists, album),
      art_url=art_url,
      artists=artists,
      comments=[comments] if comments else [],
      disc_number=DEFAULT_DISC_NO,
      length=self.get_duration(),
      name=title,
      track_id=dbus_name,
      track_number=track_no,
    )


class PlaybackMixin(Wrapper):
  @override
  def get_playstate(self) -> PlayState:
    if self.media_status.player_is_playing:
      return PlayState.PLAYING

    elif self.media_status.player_is_paused:
      return PlayState.PAUSED

    return PlayState.STOPPED

  @override
  def is_repeating(self) -> bool:
    return False

  @override
  def is_playlist(self) -> bool:
    return self.can_play_next() or self.can_play_prev()

  @override
  def get_shuffle(self) -> bool:
    return False

  @override
  def set_shuffle(self, value: bool):
    pass

  @override
  def quit(self):
    self.device.quit_app()

  @override
  def next(self):
    self.media_controller.queue_next()

  @override
  def previous(self):
    self.media_controller.queue_prev()

  @override
  def pause(self):
    self.media_controller.pause()

  @override
  def resume(self):
    self.play()

  @override
  def stop(self):
    self.media_controller.stop()

  @override
  def play(self):
    self.media_controller.play()

  @override
  def set_repeating(self, value: bool):
    pass

  @override
  def set_loop_status(self, value: LoopStatus):
    pass


class VolumeMixin(Wrapper):
  @override
  def get_volume(self) -> Volume | None:
    if status := self.cast_status:
      return Volume(status.volume_level)

    return None

  @override
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

  @override
  def is_mute(self) -> bool | None:
    if status := self.cast_status or self.media_status:
      return status.volume_muted

    return False

  @override
  def set_mute(self, value: bool):
    self.device.set_volume_muted(value)


class AbilitiesMixin(Wrapper):
  @override
  def can_quit(self) -> bool:
    return True

  @override
  def can_play(self) -> bool:
    state = self.get_playstate()

    return state is not PlayState.STOPPED

  @override
  def can_control(self) -> bool:
    return True
    # return self.can_play() or self.can_pause() \
    #   or self.can_play_next() or self.can_play_prev() \
    #   or self.can_seek()

  @override
  def can_edit_tracks(self) -> bool:
    return False

  @override
  def can_play_next(self) -> bool:
    if status := self.media_status:
      return status.supports_queue_next

    return False

  @override
  def can_play_prev(self) -> bool:
    if status := self.media_status:
      return status.supports_queue_prev

    return False

  @override
  def can_pause(self) -> bool:
    if status := self.media_status:
      return status.supports_pause

    return False

  @override
  def can_seek(self) -> bool:
    if status := self.media_status:
      return status.supports_seek

    return False


class TracklistMixin(Wrapper):
  @override
  def has_tracklist(self) -> bool:
    return bool(self.get_tracks())

  @override
  def get_tracks(self) -> list[DbusObj]:
    title, *_ = self.titles

    if title:
      return [get_track_id(title)]

    return []


class DeviceWrapper(
  AbilitiesMixin,
  ControllersMixin,
  IconsMixin,
  MetadataMixin,
  PlaybackMixin,
  StatusMixin,
  TimeMixin,
  TitlesMixin,
  TracklistMixin,
  VolumeMixin,
):
  """Wraps implementation details for device API"""

  @override
  def __init__(self, device: Device):
    self.device = device
    super().__init__()

  @override
  def __repr__(self) -> str:
    cls = type(self)

    return f'<{cls.__name__} for {self.device}>'
