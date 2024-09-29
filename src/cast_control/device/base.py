from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator
from enum import StrEnum
from itertools import chain
from typing import Any, Final, NamedTuple, Self, TYPE_CHECKING
from urllib.parse import ParseResult, parse_qs, urlparse

from iteration_utilities import unique_everseen
from pychromecast.controllers.bbciplayer import BbcIplayerController
from pychromecast.controllers.bbcsounds import BbcSoundsController
from pychromecast.controllers.bubbleupnp import BubbleUPNPController
from pychromecast.controllers.dashcast import DashCastController
from pychromecast.controllers.homeassistant_media import HomeAssistantMediaController
from pychromecast.controllers.media import DefaultMediaReceiverController
from pychromecast.controllers.multizone import MultizoneController
from pychromecast.controllers.plex import PlexController
from pychromecast.controllers.receiver import ReceiverController
from pychromecast.controllers.supla import SuplaController
from pychromecast.controllers.yleareena import YleAreenaController
from pychromecast.controllers.youtube import YouTubeController
from validators import url

from ..base import Device, MediaType

if TYPE_CHECKING:
  from ..protocols import Wrapper


URL_PROTO: Final[str] = 'https'
SKIP_FIRST: Final[slice] = slice(1, None)


class CachedIcon(NamedTuple):
  url: str
  app_id: str | None = None
  title: str | None = None


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

  # plex_api: PlexApiController | None = None
  # ha: HomeAssistantController | None= None

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

  def register(self, device: Device):
    for controller in self:
      if controller:
        device.register_handler(controller)


class Titles(NamedTuple):
  title: str | None = None
  artist: str | None = None
  album: str | None = None
  comments: str | None = None


class TitlesBuilder(Iterable[str]):
  title: str | None = None
  artist: str | None = None
  album: str | None = None
  comments: str | None = None

  _titles: deque[str]

  def __init__(
    self,
    *titles: str,
    title: str | None = None,
    artist: str | None = None,
    album: str | None = None,
    comments: str | None = None,
  ):
    self._titles = deque(titles)
    self.set(title=title, artist=artist, album=album, comments=comments)

  def __bool__(self) -> bool:
    return any(self)

  def __contains__(self, value: Any) -> bool:
    return value in iter(self)

  def __iter__(self) -> Iterator[str]:
    titles = chain(self.titles, self._titles)
    return filter(bool, titles)

  def __len__(self) -> int:
    return len(tuple(self))

  def __repr__(self) -> str:
    return repr(self.build())

  @property
  def titles(self) -> tuple[str | None, ...]:
    return self.title, self.artist, self.album, self.comments

  def add(self, *titles: str):
    titles = (title for title in titles if title and title not in self)
    self._titles.extend(titles)

  def set(
    self,
    *,
    title: str | None = None,
    artist: str | None = None,
    album: str | None = None,
    comments: str | None = None,
    overwrite: bool = True,
  ):
    if title:
      if overwrite or not self.title:
        self.title = title

      elif title not in self._titles:
        self.add(title)

    if artist:
      if overwrite or not self.artist:
        self.artist = artist

      else:
        self.add(artist)

    if album:
      if overwrite or not self.album:
        self.album = album

      else:
        self.add(album)

    if comments:
      if overwrite or not self.comments:
        self.comments = comments

      else:
        self.add(comments)

  def build(self) -> Titles:
    titles: list[str] = []
    rest: deque[str] = deque(unique_everseen(self._titles))

    for item in self.titles:
      titles.append(item if item else rest.popleft() if rest else None)

    return Titles(*titles)


class YoutubeUrl(StrEnum):
  long = 'youtube.com'
  short = 'youtu.be'

  watch_endpoint = 'watch'
  playlist_endpoint = 'playlist'

  video_query = 'v'
  playlist_query = 'list'

  video = f'{URL_PROTO}://{long}/{watch_endpoint}?{video_query}='
  playlist = f'{URL_PROTO}://{long}/{playlist_endpoint}?{playlist_query}='

  @classmethod
  def domain(cls: type[Self], uri: str | ParseResult) -> Self | None:
    match get_domain(uri):
      case cls.long:
        return cls.long

      case cls.short:
        return cls.short

    return None

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

  match YoutubeUrl.domain(uri), YoutubeUrl.type(uri):
    case YoutubeUrl.long, YoutubeUrl.video:
      qs = parse_qs(parsed.query)
      [content_id] = qs[YoutubeUrl.video_query]

    case YoutubeUrl.long, YoutubeUrl.playlist:
      qs = parse_qs(parsed.query)
      [content_id] = qs[YoutubeUrl.playlist_query]

    case YoutubeUrl.short, YoutubeUrl.video | YoutubeUrl.playlist:
      content_id = parsed.path[SKIP_FIRST]

  return content_id


def get_media_type(wrapper: Wrapper) -> MediaType | None:
  if not (status := wrapper.media_status):
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
