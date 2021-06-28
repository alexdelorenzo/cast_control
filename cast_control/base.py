from __future__ import annotations
from typing import Optional, Union
from pathlib import Path
from enum import auto

from appdirs import AppDirs
from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatus
from pychromecast.socket_client import ConnectionStatus
from pychromecast import Chromecast
from mpris_server.base import AutoName

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
USER_DIRS: Final[tuple[Path, ...]] = (
  DATA_DIR, LOG_DIR, STATE_DIR
)

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
