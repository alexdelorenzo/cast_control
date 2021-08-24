from __future__ import annotations
from typing import Optional, Union, Callable
from functools import lru_cache, partial
from pathlib import Path
from enum import auto

from app_paths import AppPaths
from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatus
from pychromecast.socket_client import ConnectionStatus
from pychromecast import Chromecast
from strenum import StrEnum

from . import NAME
from .types import Final


Seconds = int


DESKTOP_NAME: Final[str] = 'Cast Control'

RC_OK: Final[int] = 0
RC_NO_CHROMECAST: Final[int] = 1
RC_NOT_RUNNING: Final[int] = 2
RC_DAEMON_FAILED: Final[int] = 3

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
DEFAULT_SET_LOG: Final[bool] = False
LOG_LEVEL: Final[str] = 'WARN'


DESKTOP_SUFFIX: Final[str] = '.desktop'
NO_DESKTOP_FILE: Final[str] = ''

ARGS_STEM: Final[str] = '-args'
LIGHT_END: Final[str] = '-light'
DARK_END: Final[str] = '-dark'

APP_PATHS: Final[AppPaths] = AppPaths.get_paths(NAME)
DATA_DIR: Final[Path] = APP_PATHS.user_data_path
LOG_DIR: Final[Path] = APP_PATHS.user_log_path
STATE_DIR: Final[Path] = APP_PATHS.user_state_path

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
DEFAULT_ICON: Final[bool] = False

Device = Chromecast
Status = Union[MediaStatus, CastStatus, ConnectionStatus]


class NoDevicesFound(Exception):
  pass


class MediaType(StrEnum):
  GENERIC = auto()
  MOVIE = auto()
  MUSICTRACK = auto()
  PHOTO = auto()
  TVSHOW = auto()


Decorator = Callable[[Callable], Callable]


cache: Final[Decorator] = lru_cache(maxsize=LRU_MAX_SIZE)
