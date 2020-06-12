import logging

import click

from .main import main


@click.command(help="Control Chromecasts through MPRIS media controls.")
@click.option('--name', '-n', default=None, show_default=True, type=click.STRING,
              help="Specify Chromecast name, otherwise control first Chromecast found.")
@click.option('--log-level', '-l', default=logging.INFO, show_default=True,
              type=click.INT, help='Debugging log level.')
def cmd(name: str, log_level: int):
  main(name, log_level)


if __name__ == "__main__":
  cmd()
