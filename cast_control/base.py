from __future__ import annotations
from typing import Optional, Union, NamedTuple
from pathlib import Path
from uuid import UUID
from enum import auto
from os import stat_result
from functools import lru_cache
from asyncio import gather, run
from weakref import finalize
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
from .types import Final


Seconds = int


DESKTOP_NAME: Final[str] = 'Cast Control'
LOG_LEVEL: Final[str] = 'WARN'

RC_OK: Final[int] = 0
RC_NO_CHROMECAST: Final[int] = 1
RC_NOT_RUNNING: Final[int] = 2

NO_DURATION: Final[float] = 0.0
NO_DELTA: Final[int] = 0
NO_CHROMECAST_NAME: Final[str] = 'NO_NAME'
NO_STR: Final[str] = ''
NO_PORT: Final[Optional[int]] = None
NO_DEVICE: Final[str] = 'Device'

# older Python requires an explicit
# maxsize param for lru_cache()
LRU_MAX_SIZE: Final[Optional[int]] = None

YOUTUBE: Final[str] = 'YouTube'

US_IN_SEC: Final[int] = 1_000_000  # seconds to microseconds
DEFAULT_TRACK: Final[str] = '/track/1'
DEFAULT_DISC_NO: Final[int] = 1

DEFAULT_RETRY_WAIT: Final[float] = 5.0
DEFAULT_WAIT: Final[Seconds] = 30

LOG_FILE_MODE: Final[str] = 'w'  # create a new log on service start
DEFAULT_ICON: Final[bool] = False
DEFAULT_SET_LOG: Final[bool] = False

DESKTOP_SUFFIX: Final[str] = '.desktop'
NO_DESKTOP_FILE: Final[str] = ''

ARGS_STEM: Final[str] = '-args'
LIGHT_END: Final[str] = '-light'
DARK_END: Final[str] = '-dark'

APP_DIRS: Final[AppDirs] = AppDirs(NAME)
DATA_DIR: Final[Path] = Path(APP_DIRS.user_data_dir)
LOG_DIR: Final[Path] = Path(APP_DIRS.user_log_dir)
STATE_DIR: Final[Path] = Path(APP_DIRS.user_state_dir)

# use explicit parens for tuple assignment on Python <= 3.7.x
# see https://bugs.python.org/issue35814
USER_DIRS: Final[tuple[Path]] = (DATA_DIR, LOG_DIR, STATE_DIR)

PID: Final[Path] = STATE_DIR / f'{NAME}.pid'
ARGS: Final[Path] = STATE_DIR / f'service{ARGS_STEM}.tmp'
LOG: Final[Path] = LOG_DIR / f'{NAME}.log'

SRC_DIR: Final[Path] = Path(__file__).parent
ASSETS_DIR: Final[Path] = SRC_DIR / 'assets'
DESKTOP_TEMPLATE: Final[Path] = \
  ASSETS_DIR / f'template{DESKTOP_SUFFIX}'

ICON_DIR: Final[Path] = ASSETS_DIR / 'icon'
DARK_SVG: Final[Path] = ICON_DIR / 'cc-black.svg'
LIGHT_SVG: Final[Path] = ICON_DIR / 'cc-white.svg'

LIGHT_ICON = LIGHT_THUMB = LIGHT_SVG
DEFAULT_THUMB = DARK_ICON = DARK_SVG


Device = Chromecast
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


def set_log_level(
  level: str = LOG_LEVEL,
  file: Optional[Path] = None,
):
  if file:
    create_user_dirs()

  level = level.upper()

  logging.basicConfig(
    level=level,
    filename=file,
    filemode=LOG_FILE_MODE
  )


def get_stat(file: Path) -> stat_result:
  return file.stat()


@lru_cache(LRU_MAX_SIZE)
def get_src_stat() -> stat_result:
  return get_stat(SRC_DIR)


@lru_cache(LRU_MAX_SIZE)
def get_template() -> list[str]:
  return DESKTOP_TEMPLATE \
    .read_text() \
    .splitlines()


def is_older_than_module(other: Path) -> bool:
  src_stat = get_src_stat()
  other_stat = get_stat(other)

  return src_stat.st_ctime > other_stat.st_ctime


def get_paths(light_icon: bool = True) -> tuple[Path, Path]:
  icon_path = LIGHT_ICON if light_icon else DARK_ICON

  name_suffix = LIGHT_END if light_icon else DARK_END
  new_name = f'{NAME}{name_suffix}{DESKTOP_SUFFIX}'
  desktop_path = DATA_DIR / new_name

  return icon_path, desktop_path


@lru_cache(LRU_MAX_SIZE)
def new_file_from_template(file: Path, icon_path: Path):
  *lines, name, icon = get_template()
  name += DESKTOP_NAME
  icon += str(icon_path)
  lines = (*lines, name, icon)

  text = '\n'.join(lines)
  file.write_text(text)


@lru_cache(LRU_MAX_SIZE)
def create_desktop_file(light_icon: bool = True) -> Path:
  icon, file = get_paths(light_icon)

  if not file.exists() or is_older_than_module(file):
    new_file_from_template(file, icon)

  return file


async def _create_user_dirs():
  paths = map(AsyncPath, USER_DIRS)

  coros = (
    path.mkdir(parents=True, exist_ok=True)
    for path in paths
  )

  await gather(*coros)


@lru_cache(LRU_MAX_SIZE)
def create_user_dirs():
  run(_create_user_dirs())


def get_device_via_host(
  host: str,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Device]:
  info = Host(host)
  device = get_chromecast_from_host(info, retry_wait=retry_wait)

  if device:
    device.wait()
    return device

  return None  # explicit


def get_devices(
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT
) -> list[Device]:
  devices, service_browser = get_chromecasts(retry_wait=retry_wait)
  service_browser.stop_discovery()

  return devices


def get_first(devices: list[Device]) -> Device:
  first, *_ = devices
  first.wait()

  return first


def get_device_via_uuid(
  uuid: Optional[str] = None,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Device]:
  devices = get_devices(retry_wait)

  if not uuid and not devices:
    return None

  elif not uuid:
    return get_first(devices)

  uuid = UUID(uuid)

  for device in devices:
    if device.uuid == uuid:
      device.wait()

      return device

  return None


def get_device(
  name: Optional[str] = None,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Device]:
  devices = get_devices(retry_wait)

  if not name and not devices:
    return None

  elif not name:
    return get_first(devices)

  name = name.casefold()

  for device in devices:
    if device.name.casefold() == name:
      device.wait()

      return device

  return None


def find_device(
  name: Optional[str] = None,
  host: Optional[str] = None,
  uuid: Optional[str] = None,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Device]:
  device: Optional[Device] = None

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
