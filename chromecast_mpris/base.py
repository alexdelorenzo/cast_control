from typing import Optional, Union, NamedTuple
from pathlib import Path
from uuid import UUID
from enum import auto

from appdirs import AppDirs

from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatus
from pychromecast import Chromecast, get_chromecasts, \
  get_chromecast_from_host

from mpris_server.base import AutoName


RC_NO_CHROMECAST = 1
NO_DURATION = 0
NO_DELTA = 0
NO_CHROMECAST_NAME = "NO_NAME"
FIRST_CHROMECAST = 0

SRC_DIR = Path(__file__).parent
ASSETS_DIR = SRC_DIR / "assets"
DESKTOP_FILE = ASSETS_DIR / "chromecast_mpris.desktop"
LIGHT_ICON = ASSETS_DIR / 'icon' / 'cc-white.png'

DIRS = AppDirs('chromecast_mpris')
DATA_DIR = Path(DIRS.user_data_dir)
DESKTOP_FILE_DATA = DATA_DIR / DESKTOP_FILE.name

if not DATA_DIR.exists():
  DATA_DIR.mkdir()

if not DESKTOP_FILE_DATA.exists():
  *lines, last = DESKTOP_FILE.read_text().splitlines()
  last += str(LIGHT_ICON.absolute())
  lines = (*lines, last)
  data = '\n'.join(lines)
  DESKTOP_FILE_DATA.write_text(data)

DESKTOP_FILE = DESKTOP_FILE_DATA
  

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
