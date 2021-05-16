from typing import Optional, Union, NamedTuple
from pathlib import Path
from uuid import UUID
from enum import auto
import logging

from appdirs import AppDirs

from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatus
from pychromecast import Chromecast, get_chromecasts, \
  get_chromecast_from_host

from mpris_server.base import AutoName


NAME = 'chromecast_mpris'

RC_NO_CHROMECAST = 1
NO_DURATION = 0
NO_DELTA = 0
NO_CHROMECAST_NAME = "NO_NAME"
FIRST_CHROMECAST = 0

DESKTOP_SUFFIX = '.desktop'

SRC_DIR = Path(__file__).parent
ASSETS_DIR = SRC_DIR / "assets"
DESKTOP_FILE_LOCAL = ASSETS_DIR / f"{NAME}{DESKTOP_SUFFIX}"

ICON_DIR = ASSETS_DIR / 'icon'
LIGHT_ICON = ICON_DIR / 'cc-white.png'
DARK_ICON = ICON_DIR / 'cc-black.png'

APP_DIRS = AppDirs(NAME)
DATA_DIR = Path(APP_DIRS.user_data_dir)
DESKTOP_FILE_DATA = DATA_DIR / DESKTOP_FILE_LOCAL.name


def create_desktop_file(light_icon: bool = True) -> Path:
  if not DATA_DIR.exists():
    DATA_DIR.mkdir()

  if light_icon:
    icon = str(LIGHT_ICON.absolute())
    file = DATA_DIR / f'{NAME}-light{DESKTOP_SUFFIX}'

  else:
    icon = str(DARK_ICON.absolute())
    file = DATA_DIR / f'{NAME}-dark{DESKTOP_SUFFIX}'

  if not file.exists():
    *lines, last = DESKTOP_FILE_LOCAL \
      .read_text() \
      .splitlines()

    last += icon
    lines = (*lines, last)
    data = '\n'.join(lines)
    file.write_text(data)

  return file


try:
  DESKTOP_FILE_LIGHT = create_desktop_file(light_icon=True)
  DESKTOP_FILE_DARK = create_desktop_file(light_icon=False)

except Exception as e:
  logging.exception(e)
  logging.warn(f"Couldn't create {DATA_DIR} or {DESKTOP_FILE_DATA}.")
  DESKTOP_FILE_LIGHT = DESKTOP_FILE_DARK = Path()


DEFAULT_THUMB = \
  'https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/Chromecast_cast_button_icon.svg/500px-Chromecast_cast_button_icon.svg.png'
LIGHT_THUMB = \
  'https://alexdelorenzo.dev/assets/imgs/projects/chromecast_mpris/cc-white.png'

YOUTUBE = "YouTube"

NO_STR = ''
NO_PORT = None

LOG_LEVEL: str = 'WARN'

US_IN_SEC = 1_000_000  # seconds to microseconds
DEFAULT_TRACK = "/track/1"
DEFAULT_DISC_NO = 1

DEFAULT_RETRY_WAIT: float = 5.0


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


class Host(NamedTuple):
  host: str
  port: Optional[int] = NO_PORT
  uuid: str = NO_STR
  model_name: str = NO_STR
  friendly_name: str = NO_STR


def get_chromecast_via_host(
  host: str,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Chromecast]:
  info = Host(host)
  chromecast = get_chromecast_from_host(info, retry_wait=retry_wait)

  if chromecast:
    chromecast.wait()
    return chromecast

  return None  # explicit


def get_chromecast_via_uuid(
  uuid: Optional[str] = None,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Chromecast]:
  chromecasts, service_browser = get_chromecasts(retry_wait=retry_wait)

  if not uuid and not chromecasts:
    return None

  elif not uuid:
    first, *_ = chromecasts
    first.wait()

    return first

  uuid = UUID(uuid)

  for chromecast in chromecasts:
    if chromecast.uuid == uuid:
      chromecast.wait()

      return chromecast

  return None


def get_chromecast(
  name: Optional[str] = None,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Chromecast]:
  chromecasts, service_browser = get_chromecasts(retry_wait=retry_wait)

  if not name and not chromecasts:
    return None

  elif not name:
    first, *_ = chromecasts
    first.wait()

    return first

  name = name.lower()

  for chromecast in chromecasts:
    if chromecast.name.lower() == name:
      chromecast.wait()

      return chromecast

  return None
