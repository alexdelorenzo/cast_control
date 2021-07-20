from __future__ import annotations
from typing import Iterable, Optional
from subprocess import run
from enum import auto
from pathlib import Path
from functools import cache
from abc import ABC, abstractmethod

from strenum import StrEnum

from . import NAME, SHORT_NAME


NAMES: tuple[str] = NAME, SHORT_NAME


class ShellName(StrEnum):
  bash: str = auto()
  fish: str = auto()
  zsh: str = auto()


class Shell(ABC):
  name: ShellName
  src_cmd: str
  script_ext: str
  config: Optional[Path] = None

  @abstractmethod
  def create_completions(self):
    pass

  @abstractmethod
  def get_completion_path(self, app_name: str) -> Path:
    pass

  def gen_completions(self) -> Iterable[Path]:
    for app_name in NAMES:
      file = self.get_completion_path(app_name)

      cmd = self.get_cmd(self.name, app_name)
      shell_cmd = f'{cmd} > {file}'
      run(shell_cmd, shell=True)

      yield file

  def get_cmd(self, name: str) -> str:
    caps = name.upper()

    return f'_{caps}_COMPLETE={self.src_cmd} {name}'


class Bash(Shell):
  name = ShellName.bash
  src_cmd: str = 'bash_src'
  script_ext: str = 'sh'
  config: str = Path('~/.bashrc')

  def get_completion_path(self, app_name: str) -> Path:
    path = f'~/.config/{app_name}-complete.{self.script_ext}'
    return Path(path)

  def create_completions(self):
    for path in self.gen_completions():
      line = f'. {path}'
      add_line_to_file(line, self.config)


class Fish(Shell):
  name = ShellName.fish
  src_cmd: str = 'fish_src'
  script_ext: str = 'fish'

  def get_completion_path(self, app_name: str) -> Path:
    path = f'~/.config/fish/completions/{app_name}.{self.script_ext}'
    return Path(path)

  def create_completions(self):
    for _ in self.gen_completions():
      pass


class Zsh(Shell):
  name = ShellName.zsh
  src_cmd: str = 'zsh_src'
  script_ext: str = 'zsh'
  config: str = Path('~/.zshrc')

  def get_completion_path(self, app_name: str) -> Path:
    path = f'~/.config/{app_name}-complete.{self.script_ext}'
    return Path(path)

  def create_completions(self):
    for path in self.gen_completions():
      line = f'. {path}'
      add_line_to_file(line, self.config)


@cache
def add_line_to_file(line: str, path: Path):
  # check if line exists
  with path.open(mode='r') as file:
    for text in file:
      if line in text:
        return

  # write line
  with path.open(mode='a') as file:
    file.write(line)
