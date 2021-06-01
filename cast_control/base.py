from typing import Optional, Union, NamedTuple, \
  Tuple, List
from pathlib import Path
from uuid import UUID
from enum import auto
from os import stat_result
from functools import lru_cache
from asyncio import gather, run
import logging

from appdirs import AppDirs
from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatus
from pychromecast.socket_client import ConnectionStatus
from pychromecast import Chromecast, get_chromecasts, \
  get_chromecast_from_host
from mpris_server.base import AutoName
from aiopath import AsyncPath

from . import NAME


Seconds = int


DESKTOP_NAME: str = 'Cast Control'
LOG_LEVEL: str = 'WARN'

RC_OK: int = 0
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

STAT_CACHE_SIZE: int = 2

DESKTOP_SUFFIX: str = '.desktop'
NO_DESKTOP_FILE: str = ''

ARGS_STEM: str = '-args'

APP_DIRS = AppDirs(NAME)


async def get_user_dirs() -> Tuple[Path, Path, Path]:
  data_dir = AsyncPath(APP_DIRS.user_data_dir)
  log_dir = AsyncPath(APP_DIRS.user_log_dir)
  state_dir = AsyncPath(APP_DIRS.user_state_dir)
  dirs = data_dir, log_dir, state_dir

  coros = (
    dir.mkdir(parents=True, exist_ok=True)
    for dir in dirs
  )

  await gather(*coros)

  return tuple(map(Path, dirs))


DATA_DIR, LOG_DIR, STATE_DIR = run(
  get_user_dirs()
)

PID: Path = STATE_DIR / f'{NAME}.pid'
ARGS: Path = STATE_DIR / f'service{ARGS_STEM}.tmp'
LOG: Path = LOG_DIR / f'{NAME}.log'

SRC_DIR = Path(__file__).parent
ASSETS_DIR: Path = SRC_DIR / 'assets'
DESKTOP_TEMPLATE: Path = ASSETS_DIR / f'{NAME}{DESKTOP_SUFFIX}'

ICON_DIR: Path = ASSETS_DIR / 'icon'
LIGHT_THUMB = LIGHT_ICON = ICON_DIR / 'cc-white.png'
DEFAULT_THUMB = DARK_ICON = ICON_DIR / 'cc-black.png'


Status = Union[MediaStatus, CastStatus, ConnectionStatus]


class NoDevicesFound(Exception):
  pass


class MediaType(AutoName):
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


def get_device_via_host(
  host: str,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Chromecast]:
  info = Host(host)
  device = get_chromecast_from_host(info, retry_wait=retry_wait)

  if device:
    device.wait()
    return device

  return None  # explicit


def get_device_via_uuid(
  uuid: Optional[str] = None,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Chromecast]:
  devices, service_browser = get_chromecasts(retry_wait=retry_wait)

  if not uuid and not devices:
    return None

  elif not uuid:
    first, *_ = devices
    first.wait()

    return first

  uuid = UUID(uuid)

  for device in devices:
    if device.uuid == uuid:
      device.wait()

      return device

  return None


def get_device(
  name: Optional[str] = None,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Chromecast]:
  devices, service_browser = get_chromecasts(retry_wait=retry_wait)

  if not name and not devices:
    return None

  elif not name:
    first, *_ = devices
    first.wait()

    return first

  name = name.lower()

  for device in devices:
    if device.name.lower() == name:
      device.wait()

      return device

  return None


def find_device(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Chromecast]:
  device: Optional[Chromecast] = None

  if host:
    device = get_device_via_host(host, retry_wait)

  if uuid and not device:
    device = get_device_via_uuid(uuid, retry_wait)

  if name and not device:
    device = get_device(name, retry_wait)

  no_identifiers = not (host or name or uuid)

  if no_identifiers:
    device = get_device(retry_wait=retry_wait)

  return device


@lru_cache(maxsize=STAT_CACHE_SIZE)
def get_stat(file: Path) -> stat_result:
  return file.stat()


@lru_cache
def get_template() -> List[str]:
  return DESKTOP_TEMPLATE \
    .read_text() \
    .splitlines()


def is_older_than_module(other: Path) -> bool:
  src_stat = get_stat(SRC_DIR)
  other_stat = get_stat(other)

  return src_stat.st_ctime > other_stat.st_ctime


@lru_cache
def new_file_from_template(file: Path, icon_path: Path) -> Path:
  *lines, name, icon = get_template()
  name += DESKTOP_NAME
  icon += str(icon_path)
  lines = (*lines, name, icon)
  text = '\n'.join(lines)

  file.write_text(text)

  return file


@lru_cache
def create_desktop_file(light_icon: bool = True) -> Path:
  icon_path = LIGHT_ICON if light_icon else DARK_ICON
  name_suffix = '-light' if light_icon else '-dark'

  file = DATA_DIR / f'{NAME}{name_suffix}{DESKTOP_SUFFIX}'

  if file.exists() and not is_older_than_module(file):
    return file

  return new_file_from_template(file, icon_path)


def _get_user_dirs() -> Tuple[Path, Path, Path]:
  data_dir = Path(APP_DIRS.user_data_dir)
  log_dir = Path(APP_DIRS.user_log_dir)
  state_dir = Path(APP_DIRS.user_state_dir)
  dirs = data_dir, log_dir, state_dir

  for dir in dirs:
    dir.mkdir(parents=True, exist_ok=True)

  return data_dir, log_dir, state_dir
