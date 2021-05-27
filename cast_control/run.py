from __future__ import annotations
from typing import Optional, Callable, NamedTuple
from time import sleep
from pathlib import Path
from functools import partial
import pickle
import logging
import sys

from daemons.prefab.run import RunDaemon
from pychromecast import Chromecast
from mpris_server.server import Server

from .base import get_chromecast, Seconds, get_chromecast_via_host, \
  NoChromecastFoundException, LOG_LEVEL, get_chromecast_via_uuid, \
  DEFAULT_RETRY_WAIT, RC_NO_CHROMECAST, DATA_DIR, NAME, LOG, \
  RC_NOT_RUNNING, PID, NO_DEVICE, DEFAULT_WAIT, ARGS, find_device
from .adapter import ChromecastAdapter
from .listeners import register_mpris_adapter


LOG_FILE_MODE: str = 'w'  # create a new log file on each run


FuncMaybe = Optional[Callable]


class MprisDaemon(RunDaemon):
  target: FuncMaybe = None
  args: ArgsMaybe = None

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
    self.target = partial(func, *args)

  def setup_logging(self):
    if not self.args:
      return

    set_log_level(self.args.log_level, file=LOG)

  def run(self):
    if not self.target:
      return

    self.setup_logging()
    self.target()


class DaemonArgs(NamedTuple):
  name: Optional[str]
  host: Optional[str]
  uuid: Optional[str]
  wait: Optional[float]
  retry_wait: Optional[float]
  icon: bool
  log_level: str

  @property
  def file(self) -> Path:
    name, host, uuid, *_ = self
    device = name or host or uuid or NO_DEVICE

    return ARGS.with_stem(f'{device}-args')

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

  chromecast_adapter = ChromecastAdapter(device)
  mpris = Server(name=device.name, adapter=chromecast_adapter)
  mpris.publish()

  register_mpris_adapter(device, mpris, chromecast_adapter)

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
  icon: bool = False,
  log_level: str = LOG_LEVEL
):
  set_log_level(log_level)
  mpris = retry_until_found(name, host, uuid, wait, retry_wait)

  if mpris and icon:
    mpris.adapter.wrapper.set_icon(True)

  if not mpris:
    device = name or host or uuid or NO_DEVICE
    raise NoChromecastFoundException(device)

  mpris.loop()


def run_safe(
  name: Optional[str],
  host: Optional[str],
  uuid: Optional[str],
  wait: Optional[float],
  retry_wait: Optional[float],
  icon: bool,
  log_level: str
):
  try:
    run_server(
      name,
      host,
      uuid,
      wait,
      retry_wait,
      icon,
      log_level
    )

  except NoChromecastFoundException as e:
    logging.warning(f"{e} not found")
    sys.exit(RC_NO_CHROMECAST)
