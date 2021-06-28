from __future__ import annotations
from typing import Optional, Callable, NamedTuple
from functools import partial
from pathlib import Path
import pickle

from daemons.prefab.run import RunDaemon

from ..base import LOG_LEVEL, PID, \
  DEFAULT_RETRY_WAIT, NAME, LOG, \
  NO_DEVICE, DEFAULT_WAIT, ARGS, \
  ARGS_STEM, DEFAULT_ICON, DEFAULT_SET_LOG
from .state import setup_logging


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

    setup_logging(level, file=LOG)

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
  def load(identifier: Optional[str] = None) -> ArgsMaybe:
    if identifier:
      args = ARGS.with_stem(f'{identifier}{ARGS_STEM}')

    else:
      args = ARGS

    if args.exists():
      dump = args.read_bytes()
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
