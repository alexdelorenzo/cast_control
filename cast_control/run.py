from __future__ import annotations
from typing import Optional, Callable, NamedTuple, Tuple
from time import sleep
from pathlib import Path
from functools import partial
import pickle
import logging
import sys

from daemons.prefab.run import RunDaemon
from pychromecast import Chromecast
from mpris_server.server import Server

from .base import Seconds, NoDevicesFound, LOG_LEVEL, \
  DEFAULT_RETRY_WAIT, RC_NO_CHROMECAST, DATA_DIR, NAME, LOG, \
  RC_NOT_RUNNING, PID, NO_DEVICE, DEFAULT_WAIT, ARGS, find_device, \
  ARGS_STEM
from .adapter import CastAdapter
from .listeners import register_mpris_adapter


LOG_FILE_MODE: str = 'w'  # create a new log on service start
DEFAULT_ICON: bool = False
DEFAULT_SET_LOG: bool = False


FuncMaybe = Optional[Callable]


class MprisDaemon(RunDaemon):
  target: FuncMaybe = None
  args: ArgsMaybe = None
  _logging: Optional[str] = None

  @property
  def logging(self) -> Optional[str]:
    return self._logging

  @logging.setter
  def logging(self, val: Optional[str]):
    self._logging = val

  def set_target(
    self,
    func: FuncMaybe = None,
    *args,
    **kwargs
  ):
    if not func:
      self.target = None
      return

    self.target = partial(func, *args, **kwargs)

  def set_target_via_args(
    self,
    func: FuncMaybe = None,
    args: ArgsMaybe = None
  ):
    if not func:
      self.target = None
      return

    self.args = args
    self.logging = args.set_logging
    self.target = partial(func, args)

  def setup_logging(self):
    if self.args:
      level = self.args.log_level

    else:
      level = self.logging

    set_log_level(level, file=LOG)

  def run(self):
    if not self.target:
      return

    self.setup_logging()
    self.target()


class DaemonArgs(NamedTuple):
  name: Optional[str] = None
  host: Optional[str] = None
  uuid: Optional[str] = None
  wait: Optional[float] = DEFAULT_WAIT
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT
  icon: bool = DEFAULT_ICON
  log_level: str = LOG_LEVEL
  set_logging: bool = DEFAULT_SET_LOG

  @staticmethod
  def load() -> ArgsMaybe:
    if ARGS.exists():
      dump = ARGS.read_bytes()
      return pickle.loads(dump)

    return None

  @staticmethod
  def delete():
    if ARGS.exists():
      ARGS.unlink()

  def save(self) -> Path:
    dump = pickle.dumps(self)
    ARGS.write_bytes(dump)

  @property
  def file(self) -> Path:
    name, host, uuid, *_ = self
    device = name or host or uuid or NO_DEVICE

    return ARGS.with_stem(f'{device}{ARGS_STEM}')


ArgsMaybe = Optional[DaemonArgs]


def get_daemon(
  func: FuncMaybe = None,
  *args,
  _pidfile: str = str(PID),
  **kwargs,
) -> MprisDaemon:
  daemon = MprisDaemon(pidfile=_pidfile)
  daemon.set_target(func, *args, **kwargs)

  return daemon


def get_daemon_from_args(
  func: FuncMaybe = None,
  args: ArgsMaybe = None,
  _pidfile: str = str(PID),
) -> MprisDaemon:
  daemon = MprisDaemon(pidfile=_pidfile)
  daemon.set_target_via_args(func, args)

  return daemon


def set_log_level(
  level: str = LOG_LEVEL,
  file: Optional[Path] = None,
):
  level = level.upper()
  logging.basicConfig(
    level=level,
    filename=file,
    filemode=LOG_FILE_MODE
  )


def create_adapters_and_server(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Server]:
  device = find_device(name, host, uuid, retry_wait)

  if not device:
    return None

  adapter = CastAdapter(device)
  mpris = Server(name=device.name, adapter=adapter)
  mpris.publish()

  register_mpris_adapter(device, mpris, adapter)

  return mpris


def retry_until_found(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[Seconds] = DEFAULT_WAIT,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
) -> Optional[Server]:
  """
    If the Chromecast isn't found, keep trying to find it.

    If `wait` is None, then retrying is disabled.
  """

  while True:
    mpris = create_adapters_and_server(name, host, uuid, retry_wait)

    if mpris or wait is None:
      return mpris

    device = name or host or uuid or NO_DEVICE
    logging.info(f"{device} not found. Waiting {wait} seconds before retrying.")
    sleep(wait)


def run_server(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[float] = DEFAULT_WAIT,
  retry_wait: Optional[float] = DEFAULT_RETRY_WAIT,
  icon: bool = DEFAULT_ICON,
  log_level: str = LOG_LEVEL,
  set_logging: bool = DEFAULT_SET_LOG,
):
  if set_logging:
    set_log_level(log_level)

  mpris = retry_until_found(name, host, uuid, wait, retry_wait)

  if mpris and icon:
    mpris.adapter.set_icon(True)

  if not mpris:
    device = name or host or uuid or NO_DEVICE
    raise NoDevicesFound(device)

  mpris.loop()


def run_safe(
  args: DaemonArgs
):
  try:
    run_server(*args)

  except NoDevicesFound as e:
    logging.warning(f"{e} not found")
    sys.exit(RC_NO_CHROMECAST)
