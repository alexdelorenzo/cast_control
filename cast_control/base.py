from __future__ import annotations

from collections.abc import Callable
from decimal import Context, Decimal, ROUND_HALF_UP, getcontext
from enum import IntEnum, StrEnum, auto
from functools import lru_cache
from pathlib import Path
from typing import Final

from app_paths import AsyncAppPaths, get_paths
from pychromecast import Chromecast
from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatus, LaunchFailure
from pychromecast.socket_client import ConnectionStatus

from . import NAME, __author__, __version__


Seconds = Decimal

DESKTOP_NAME: Final[str] = 'Cast Control'
LOG_LEVEL: Final[str] = 'WARN'

NO_DURATION: Final[int] = 0
NO_DELTA: Final[int] = 0
NO_DEVICE_NAME: Final[str] = 'NO_NAME'
NO_STR: Final[str] = ''
NO_PORT: Final[int | None] = None

# older Python requires an explicit
# maxsize param for lru_cache()
SINGLETON: Final[int] = 1

YOUTUBE: Final[str] = 'YouTube'

US_IN_SEC: Final[int] = 1_000_000  # seconds to microseconds
DEFAULT_TRACK: Final[str] = '/track/1'
DEFAULT_DISC_NO: Final[int] = 1

DEFAULT_RETRY_WAIT: Final[Seconds] = Seconds(5.0)
DEFAULT_WAIT: Final[Seconds] = Seconds(30)
DEFAULT_DEVICE_NAME: Final[str] = DESKTOP_NAME
DEFAULT_NO_DEVICE_NAME: Final[str] = 'Device'

LOG_FILE_MODE: Final[str] = 'w'  # create a new log on service start
DEFAULT_ICON: Final[bool] = False
DEFAULT_SET_LOG: Final[bool] = False

DESKTOP_SUFFIX: Final[str] = '.desktop'
NO_DESKTOP_FILE: Final[str] = ''

ARGS_STEM: Final[str] = '-args'
LIGHT_END: Final[str] = '-light'
DARK_END: Final[str] = '-dark'

PATHS: Final[AsyncAppPaths] = get_paths(
  NAME,
  __author__,
  __version__,
  is_async=True
)
DATA_DIR: Final[Path] = Path(PATHS.user_data_path)
LOG_DIR: Final[Path] = Path(PATHS.user_log_path)
STATE_DIR: Final[Path] = Path(PATHS.user_state_path)

USER_DIRS: Final[tuple[Path, ...]] = DATA_DIR, LOG_DIR, STATE_DIR

PID: Final[Path] = STATE_DIR / f'{NAME}.pid'
ARGS: Final[Path] = STATE_DIR / f'service{ARGS_STEM}.tmp'
LOG: Final[Path] = LOG_DIR / f'{NAME}.log'

SRC_DIR: Final[Path] = Path(__file__).parent
ASSETS_DIR: Final[Path] = SRC_DIR / 'assets'
DESKTOP_TEMPLATE: Final[Path] = ASSETS_DIR / f'template{DESKTOP_SUFFIX}'

ICON_DIR: Final[Path] = ASSETS_DIR / 'icon'
DARK_SVG: Final[Path] = ICON_DIR / 'cc-black.svg'
LIGHT_SVG: Final[Path] = ICON_DIR / 'cc-white.svg'
TEMPLATE_SVG: Final[Path] = ICON_DIR / 'cc-template.svg'

LIGHT_ICON = LIGHT_THUMB = LIGHT_SVG
DEFAULT_THUMB = DARK_ICON = DARK_SVG

PRECISION: Final[int] = 4
CONTEXT: Final[Context] = getcontext()
CONTEXT.prec = PRECISION
CONTEXT.rounding = ROUND_HALF_UP

Device = Chromecast
Status = MediaStatus | CastStatus | ConnectionStatus | LaunchFailure

type Decorated[** P, T] = Callable[P, T]
type Decoratable[** P, T] = Callable[P, T]
type Decorator[** P, T] = Callable[[Decoratable], Decorated]


class NoDevicesFound(Exception):
  pass


class MediaType(StrEnum):
  GENERIC = auto()
  MOVIE = auto()
  MUSICTRACK = auto()
  PHOTO = auto()
  TVSHOW = auto()


class Rc(IntEnum):
  OK = 0
  NO_DEVICE = auto()
  NOT_RUNNING = auto()


singleton: Final[Decorator] = lru_cache(SINGLETON)
