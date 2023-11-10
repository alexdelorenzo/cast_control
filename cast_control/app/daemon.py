from __future__ import annotations

import pickle
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import NamedTuple

from daemons.prefab.run import RunDaemon

from .state import setup_logging
from ..base import ARGS, ARGS_STEM, DEFAULT_ICON, DEFAULT_RETRY_WAIT, DEFAULT_SET_LOG, \
  DEFAULT_WAIT, LOG, LOG_LEVEL, NO_DEVICE, PID, Seconds


class MprisDaemon[**P, T](RunDaemon):
  target: Callable[P, T] | None = None
  args: DaemonArgs | None = None
  _logging: str | None = None

  @property
  def logging(self) -> str | None:
    return self._logging

  @logging.setter
  def logging(self, val: str | None):
    self._logging = val

  def set_target[**P, T](
    self,
    func: Callable[P, T] | None = None,
    *args,
    **kwargs
  ):
    if not func:
      self.target = None
      return

    self.target = partial(func, *args, **kwargs)

  def set_target_via_args[**P, T](
    self,
    func: Callable[P, T] | None = None,
    args: DaemonArgs | None = None
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
  name: str | None = None
  host: str | None = None
  uuid: str | None = None
  wait: Seconds | None = DEFAULT_WAIT
  retry_wait: Seconds | None = DEFAULT_RETRY_WAIT
  icon: bool = DEFAULT_ICON
  log_level: str = LOG_LEVEL
  set_logging: bool = DEFAULT_SET_LOG

  @staticmethod
  def load(identifier: str | None = None) -> DaemonArgs | None:
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

    return ARGS

  @property
  def file(self) -> Path:
    name, host, uuid, *_ = self
    device = name or host or uuid or NO_DEVICE

    return ARGS.with_stem(f'{device}{ARGS_STEM}')


def get_daemon[**P, T](
  func: Callable[P, T] | None = None,
  *args,
  _pidfile: str = str(PID),
  **kwargs,
) -> MprisDaemon:
  daemon = MprisDaemon(pidfile=_pidfile)
  daemon.set_target(func, *args, **kwargs)

  return daemon


def get_daemon_from_args[**P, T](
  func: Callable[P, T] | None = None,
  args: DaemonArgs | None = None,
  _pidfile: str = str(PID),
) -> MprisDaemon:
  daemon = MprisDaemon(pidfile=_pidfile)
  daemon.set_target_via_args(func, args)

  return daemon
