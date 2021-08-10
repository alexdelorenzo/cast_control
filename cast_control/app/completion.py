from __future__ import annotations
from typing import Iterable, Optional
from abc import ABC, abstractmethod
from functools import cache
from pathlib import Path
from subprocess import run
from enum import auto

from strenum import StrEnum

from .. import NAME, SHORT_NAME


NAMES: tuple[str, str] = (NAME, SHORT_NAME)
REPLACE: tuple[str, str] = ('-', '_')
NEW_LINE: str = '\n'


class ShellName(StrEnum):
  bash: str = auto()
  fish: str = auto()
  zsh: str = auto()


class Shell(ABC):
  name: ShellName
  src_cmd: str
  extension: str
  config: Optional[Path] = None

  @abstractmethod
  def get_completion_path(self, name: str) -> Path:
    pass

  @abstractmethod
  def create_completions(self):
    pass

  def create_completion_path(self, name: str) -> Path:
    file = self.get_completion_path(app_name)
    file.parent.mkdir(parents=True, exist_ok=True)

    return file

  def get_cmd(self, name: str) -> str:
    caps = name.upper()
    caps = caps.replace(*REPLACE)

    return f'_{caps}_COMPLETE={self.src_cmd} {name}'

  def run_cmd(self, name: str, file: Path):
    completion_cmd = self.get_cmd(name)
    shell_cmd = f'{completion_cmd} > {file}'
    run(shell_cmd, shell=True)

  def gen_completions(self) -> Iterable[Path]:
    for app_name in NAMES:
      file = self.create_completion_path(app_name)
      self.run_cmd(app_name, file)

      yield file


class Bash(Shell):
  name: ShellName = ShellName.bash
  src_cmd: str = 'bash_source'
  extension: str = 'sh'
  config: Path = Path('~/.bashrc')

  def get_completion_path(self, name: str) -> Path:
    path = f'~/.config/{name}-complete.{self.extension}'
    return Path(path)

  def create_completions(self):
    for path in self.gen_completions():
      line = f'. {path}'
      add_line_to_file(line, self.config)


class Fish(Shell):
  name: ShellName = ShellName.fish
  src_cmd: str = 'fish_source'
  extension: str = 'fish'

  def get_completion_path(self, name: str) -> Path:
    path = f'~/.config/fish/completions/{name}.{self.extension}'
    return Path(path)

  def create_completions(self):
    for _ in self.gen_completions():
      pass


class Zsh(Shell):
  name: ShellName = ShellName.zsh
  src_cmd: str = 'zsh_source'
  extension: str = 'zsh'
  config: Path = Path('~/.zshrc')

  def get_completion_path(self, name: str) -> Path:
    path = f'~/.config/{name}-complete.{self.extension}'
    return Path(path)

  def create_completions(self):
    for path in self.gen_completions():
      line = f'. {path}'
      add_line_to_file(line, self.config)


SHELLS: dict[ShellName, Shell] = {
  ShellName.bash: Bash(),
  ShellName.fish: Fish(),
  ShellName.zsh: Zsh(),
}


def get_shell(shell: ShellName) -> Shell:
  return SHELLS[shell]


@cache
def add_line_to_file(line: str, path: Path):
  if not line.endswith(NEW_LINE):
    line += NEW_LINE

  path = path.expanduser()

  # check if line exists
  with path.open(mode='r') as file:
    for text in file:
      if line in text:
        return

  # write line
  with path.open(mode='a') as file:
    file.write(line)
