from abc import ABC
from typing import Optional, Any, Union, NamedTuple
from pathlib import Path
from enum import auto

from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.youtube import YouTubeController
from pychromecast.socket_client import CastStatus
from pychromecast import Chromecast, get_chromecasts, \
  get_chromecast_from_host

from mpris_server.base import AutoName


RC_NO_CHROMECAST = 1
NO_DURATION = 0
NO_DELTA = 0
NO_CHROMECAST_NAME = "NO_NAME"
FIRST_CHROMECAST = 0

DESKTOP_FILE = Path(__file__).parent / "chromecast_mpris.desktop"
DEFAULT_THUMB = 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Chromecast_cast_button_icon.svg/500px-Chromecast_cast_button_icon.svg.png'

YOUTUBE = "YouTube"

NO_STR = ''
NO_PORT = None

LOG_LEVEL: str = 'WARN'


Seconds = int
Status = Union[MediaStatus, CastStatus]


class NoChromecastFoundException(Exception):
  pass


class ChromecastMediaType(AutoName):
  GENERIC = auto()
  MOVIE = auto()
  MUSICTRACK = auto()
  PHOTO = auto()
  TVSHOW = auto()


class Wrapper(ABC):
  @property
  def cast_status(self) -> Optional[CastStatus]:
    pass

  @property
  def media_status(self) -> Optional[MediaStatus]:
    pass

  def can_play_next(self) -> bool:
    pass

  def can_play_prev(self) -> bool:
    pass

  def play_next(self):
    pass

  def play_prev(self):
    pass


class ChromecastWrapper(Wrapper):
  """
  A wrapper to make it easier to switch out backend implementations.

  Holds common logic for dealing with underlying Chromecast API.
  """

  def __init__(self, cc: Chromecast):
    self.cc = cc
    self.yt_ctl = YouTubeController()
    self.cc.register_handler(self.yt_ctl)

  def __getattr__(self, name: str) -> Any:
    return getattr(self.cc, name)

  def __repr__(self) -> str:
    return f"<{self.__name__} for {self.cc}>"

  @property
  def cast_status(self) -> Optional[CastStatus]:
    return self.cc.status

  @property
  def media_status(self) -> Optional[MediaStatus]:
    return self.cc.media_controller.status

  def can_play_next(self) -> bool:
    return self.media_status.supports_queue_next

  def can_play_prev(self) -> bool:
    return self.media_status.supports_queue_next

  def play_next(self):
    self.cc.media_controller.queue_next()

  def play_prev(self):
    self.cc.media_controller.queue_prev()


class Host(NamedTuple):
  host: str
  port: Optional[int] = NO_PORT
  uuid: str = NO_STR
  model_name: str = NO_STR
  friendly_name: str = NO_STR


def get_chromecast_via_host(host: str) -> Optional[Chromecast]:
  info = Host(host)
  chromecast = get_chromecast_from_host(info)

  if chromecast:
    chromecast.wait()
    return chromecast

  return None  # be explicit


def get_chromecast(name: Optional[str] = None) -> Optional[Chromecast]:
  chromecasts, service_browser = get_chromecasts()

  if not name and not chromecasts:
    return

  elif not name:
    chromecast = chromecasts[FIRST_CHROMECAST]
    chromecast.wait()
    return chromecast

  name = name.lower()

  for chromecast in chromecasts:
    if chromecast.name.lower() == name:
      chromecast.wait()
      return chromecast

