from typing import Optional, Union, NamedTuple, \
  Tuple
from pathlib import Path
from uuid import UUID
from enum import auto
import logging

from appdirs import AppDirs
from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatus
from pychromecast.socket_client import ConnectionStatus
from pychromecast import Chromecast, get_chromecasts, \
  get_chromecast_from_host
from mpris_server.base import AutoName


Seconds = int


NAME: str = 'cast_control'
DESKTOP_NAME: str = 'Cast Control'
LOG_LEVEL: str = 'WARN'

RC_NO_CHROMECAST: int = 1
RC_NOT_RUNNING: int = 2

NO_DURATION: float = 0.0
NO_DELTA: int = 0
NO_CHROMECAST_NAME: str = 'NO_NAME'
NO_STR: str = ''
NO_PORT: Optional[int] = None
NO_DEVICE: str = 'Device'

YOUTUBE: str = 'YouTube'

US_IN_SEC: int = 1_000_000  # seconds to microseconds
DEFAULT_TRACK: str = '/track/1'
DEFAULT_DISC_NO: int = 1

DEFAULT_RETRY_WAIT: float = 5.0
DEFAULT_WAIT: Seconds = 30

DESKTOP_SUFFIX: str = '.desktop'
NO_DESKTOP_FILE: str = ''

APP_DIRS = AppDirs(NAME)


def get_user_dirs() -> Tuple[Path, Path, Path]:
  data_dir = Path(APP_DIRS.user_data_dir)
  log_dir = Path(APP_DIRS.user_log_dir)
  state_dir = Path(APP_DIRS.user_state_dir)
  dirs = data_dir, log_dir, state_dir

  for dir in dirs:
    dir.mkdir(parents=True, exist_ok=True)

  return data_dir, log_dir, state_dir


DATA_DIR, LOG_DIR, STATE_DIR = get_user_dirs()

PID: Path = STATE_DIR / f'{NAME}.pid'
ARGS: Path = STATE_DIR / 'service-args.tmp'
LOG: Path = LOG_DIR / f'{NAME}.log'

SRC_DIR = Path(__file__).parent
ASSETS_DIR: Path = SRC_DIR / 'assets'
DESKTOP_TEMPLATE: Path = ASSETS_DIR / f'{NAME}{DESKTOP_SUFFIX}'

ICON_DIR: Path = ASSETS_DIR / 'icon'
LIGHT_THUMB = LIGHT_ICON = ICON_DIR / 'cc-white.png'
DEFAULT_THUMB = DARK_ICON = ICON_DIR / 'cc-black.png'


def create_desktop_file(light_icon: bool = True) -> Path:
  if light_icon:
    path = LIGHT_ICON
    name_suffix = '-light'

  else:
    path = DARK_ICON
    name_suffix = '-dark'

  icon_path = str(path.absolute())
  file = DATA_DIR / f'{NAME}{name_suffix}{DESKTOP_SUFFIX}'

  *lines, name, icon = DESKTOP_TEMPLATE \
    .read_text() \
    .splitlines()

  name += DESKTOP_NAME
  icon += icon_path
  lines = (*lines, name, icon)
  data = '\n'.join(lines)

  if not file.exists() or data != file.read_text():
    file.write_text(data)

  return file


DESKTOP_FILE_LIGHT: Optional[Path] = None
DESKTOP_FILE_DARK: Optional[Path] = None

try:
  DESKTOP_FILE_LIGHT = create_desktop_file(light_icon=True)
  DESKTOP_FILE_DARK = create_desktop_file(light_icon=False)

except Exception as e:
  logging.exception(e)
  logging.warning(f"Couldn't create {DESKTOP_SUFFIX} files in {DATA_DIR}.")


Status = Union[MediaStatus, CastStatus, ConnectionStatus]


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
