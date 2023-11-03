from __future__ import annotations

from decimal import Context, Decimal, ROUND_HALF_UP, ROUND_UP, getcontext
from enum import StrEnum, auto
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional, ParamSpec, TypeVar, Union, Final

from app_paths import AsyncAppPaths, get_paths
from pychromecast import Chromecast
from pychromecast.controllers.media import MediaStatus
from pychromecast.controllers.receiver import CastStatus
from pychromecast.socket_client import ConnectionStatus

from . import NAME, __author__, __version__


Seconds = Decimal


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
SINGLETON: Final[int] = 1

YOUTUBE: Final[str] = 'YouTube'

US_IN_SEC: Final[int] = 1_000_000  # seconds to microseconds
DEFAULT_TRACK: Final[str] = '/track/1'
DEFAULT_DISC_NO: Final[int] = 1

DEFAULT_RETRY_WAIT: Final[Seconds] = Seconds(5.0)
DEFAULT_WAIT: Final[Seconds] = Seconds(30)
DEFAULT_NAME: Final[str] = DESKTOP_NAME

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
DESKTOP_TEMPLATE: Final[Path] = \
  ASSETS_DIR / f'template{DESKTOP_SUFFIX}'

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
Status = Union[MediaStatus, CastStatus, ConnectionStatus]

T = TypeVar('T')
P = ParamSpec('P')

Decorated = Callable[P, T]
Decoratable = Callable[P, T]
Decorator = Callable[[Decoratable], Decorated]


class NoDevicesFound(Exception):
  pass


class MediaType(StrEnum):
  GENERIC = auto()
  MOVIE = auto()
  MUSICTRACK = auto()
  PHOTO = auto()
  TVSHOW = auto()


singleton: Final[Decorator] = lru_cache(SINGLETON)
