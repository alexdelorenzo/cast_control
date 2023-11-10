from __future__ import annotations

import logging
from asyncio import gather, run
from collections.abc import Callable
from functools import cache, wraps
from os import stat_result
from pathlib import Path

from aiopath import AsyncPath
from rich.logging import RichHandler

from ..base import DARK_END, DARK_ICON, DATA_DIR, DESKTOP_NAME, DESKTOP_SUFFIX, DESKTOP_TEMPLATE, LIGHT_END, \
  LIGHT_ICON, LOG_FILE_MODE, LOG_LEVEL, NAME, PATHS, SRC_DIR, USER_DIRS, singleton


type Decoratable[**P, T] = Callable[P, T]
type Decorated[**P, T] = Callable[P, T]


def setup_logging(
  level: str = LOG_LEVEL,
  file: Path | None = None,
):
  level = level.upper()

  if file:
    create_user_dirs()

    logging.basicConfig(
      level=level,
      filename=file,
      filemode=LOG_FILE_MODE,
    )

  else:
    handlers = [RichHandler(rich_tracebacks=True)]
    logging.basicConfig(level=level, handlers=handlers)


# check for user dirs and create them asynchronously
async def _create_user_dirs():
  await PATHS.create_user_paths()

  paths = map(AsyncPath, USER_DIRS)
  coros = (path.mkdir(parents=True, exist_ok=True) for path in paths)

  await gather(*coros)


@singleton
def create_user_dirs():
  run(_create_user_dirs())


def ensure_user_dirs_exist[**P, T](func: Decoratable) -> Decorated:
  @wraps(func)
  def new_func(*args: P.args, **kwargs: P.kwargs) -> T:
    create_user_dirs()
    return func(*args, **kwargs)

  return new_func


def get_stat(file: Path) -> stat_result:
  return file.stat()


@singleton
def get_src_stat() -> stat_result:
  return get_stat(SRC_DIR)


@singleton
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
