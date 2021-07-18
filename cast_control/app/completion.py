from __future__ import annotations
from typing import Iterable
from subprocess import run
from enum import auto
from pathlib import Path
from functools import cache

from strenum import StrEnum

from . import NAME, SHORT_NAME


NAMES: tuple[str] = NAME, SHORT_NAME


class Shell(StrEnum):
  bash: str = auto()
  fish: str = auto()
  zsh: str = auto()


SRC_CMDS: dict[Shell, str] = {
  Shell.bash: 'bash_source',
  Shell.fish: 'fish_source',
  Shell.zsh: 'zsh_source'
}


EXTS: dict[Shell, str] = {
  Shell.bash: 'sh',
  Shell.fish: 'fish',
  Shell.zsh: 'zsh'
}


CFGS: dict[Shell, Path] = {
  Shell.bash: Path('~/.bashrc'),
  Shell.zsh: Path('~/.zshrc'),
}


def get_cmd(shell: Shell, name: str) -> str:
  src_cmd = SRC_CMDS[shell]
  caps = name.upper()

  return f"_{caps}_COMPLETE={src_cmd} {name}"


def gen_fish_completions() -> Iterable[Path]:
  shell = Shell.fish
  ext = EXTS[shell]

  for name in NAMES:
    file = Path(f"~/.config/fish/completions/{name}.{ext}")

    cmd = get_cmd(shell, name)
    shell_cmd = f"{cmd} > {file}"
    run(shell_cmd, shell=True)

    yield file


def gen_bash_completions() -> Iterable[Path]:
  shell = Shell.bash
  ext = EXTS[shell]

  for name in NAMES:
    file = Path(f"~/.config/{name}-complete.{ext}")

    cmd = get_cmd(shell, name)
    shell_cmd = f"{cmd} > {file}"
    run(shell_cmd, shell=True)

    yield file


def gen_zsh_completions() -> Iterable[Path]:
  shell = Shell.zsh
  ext = EXTS[shell]

  for name in NAMES:
    file = Path(f"~/.config/{name}-complete.{ext}")

    cmd = get_cmd(shell, name)
    shell_cmd = f"{cmd} > {file}"
    run(shell_cmd, shell=True)

    yield file


@cache
def add_line_to_file(line: str, path: Path):
  text = path.read_text()

  if line in text:
    return

  with path.open(mode='a') as file:
    file.write(line)


def do_fish():
  for _ in gen_fish_completions():
    pass


def do_bash():
  cfg = CFGS[Shell.bash]

  for path in gen_bash_completions():
    line = f". {path}"
    add_line_to_file(line, cfg)


def do_zsh():
  cfg = CFGS[Shell.zsh]

  for path in gen_zsh_completions():
    line = f". {path}"
    add_line_to_file(line, cfg)
