from __future__ import annotations
from typing import Optional, Callable
from pathlib import Path
from os import stat_result
from functools import lru_cache, wraps
from asyncio import gather, run
import logging

from aiopath import AsyncPath

from ..base import USER_DIRS, LRU_MAX_SIZE, DESKTOP_NAME, \
  DESKTOP_TEMPLATE, DESKTOP_SUFFIX, SRC_DIR, LIGHT_END, \
  LIGHT_ICON, DARK_END, DARK_ICON, DATA_DIR, LOG_LEVEL, \
  LOG_FILE_MODE, NAME


def setup_logging(
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


# check for user dirs and create them asynchronously
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


def ensure_user_dirs_exist(func: Callable) -> Callable:
  @wraps(func)
  def new_func(*args, **kwargs):
    create_user_dirs()
    return func(*args, **kwargs)

  return new_func


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

  return desktop_path, icon_path


@lru_cache(LRU_MAX_SIZE)
def new_file_from_template(file: Path, icon_path: Path):
  *lines, name, icon = get_template()
  name += DESKTOP_NAME
  icon += str(icon_path)
  lines = (*lines, name, icon)
  text = '\n'.join(lines)

  file.write_text(text)


@lru_cache(LRU_MAX_SIZE)
@ensure_user_dirs_exist
def create_desktop_file(light_icon: bool = True) -> Path:
  file, icon = get_paths(light_icon)

  if not file.exists() or is_older_than_module(file):
    new_file_from_template(file, icon)

  return file
