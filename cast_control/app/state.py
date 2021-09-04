from __future__ import annotations
from typing import Optional, Callable, Any
from pathlib import Path
from os import stat_result
from functools import wraps
from asyncio import gather, run
import logging
import logging.handlers

from aiopath import AsyncPath

from ..types import Final
from ..base import USER_DIRS, LRU_MAX_SIZE, DESKTOP_NAME, \
  DESKTOP_TEMPLATE, DESKTOP_SUFFIX, SRC_DIR, LIGHT_END, \
  LIGHT_ICON, DARK_END, DARK_ICON, DATA_DIR, LOG_LEVEL, \
  LOG_FILE_MODE, NAME, APP_PATHS, cache, Decorator


MAX_LOG_SIZE: Final[Bytes] = 4 * 1024 ** 2  # bytes
LOG_BACKUPS: Final[int] = 1


def setup_logging(
  level: str = LOG_LEVEL,
  file: Optional[Path] = None,
):
  level = level.upper()
  handlers: list[logging.Handler] = []

  if file:
    create_user_dirs()

    handler = logging.handlers.RotatingFileHandler(
      filename=file,
      mode=LOG_FILE_MODE,
      maxBytes=MAX_LOG_SIZE,
      backupCount=LOG_BACKUPS,
    )
    handlers.append(handler)

  logging.basicConfig(
    level=level,
    handlers=handlers,
  )


@cache
def create_user_dirs():
  APP_PATHS.create_user_paths()


def ensure_user_dirs_exist(func: Callable) -> Callable:
  @wraps(func)
  def new_func(*args, **kwargs) -> Any:
    create_user_dirs()
    return func(*args, **kwargs)

  return new_func


@cache
def get_src_stat() -> stat_result:
  return SRC_DIR.stat()


@cache
def get_template() -> list[str]:
  return DESKTOP_TEMPLATE \
    .read_text() \
    .splitlines()


def is_older_than_module(other: Path) -> bool:
  src_stat = get_src_stat()
  other_stat = other.stat()

  return src_stat.st_ctime > other_stat.st_ctime


def get_paths(light_icon: bool = True) -> tuple[Path, Path]:
  icon_path = LIGHT_ICON if light_icon else DARK_ICON
  name_suffix = LIGHT_END if light_icon else DARK_END
  new_name = f'{NAME}{name_suffix}{DESKTOP_SUFFIX}'
  desktop_path = DATA_DIR / new_name

  return desktop_path, icon_path


@cache
def new_file_from_template(file: Path, icon_path: Path):
  *lines, name, icon = get_template()
  name += DESKTOP_NAME
  icon += str(icon_path)

  lines = (*lines, name, icon)
  text = '\n'.join(lines)
  file.write_text(text)


@cache
@ensure_user_dirs_exist
def create_desktop_file(light_icon: bool = True) -> Path:
  file, icon = get_paths(light_icon)

  if not file.exists() or is_older_than_module(file):
    new_file_from_template(file, icon)

  return file
