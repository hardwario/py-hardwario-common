import os
import sys
import pkgutil
import importlib
import click
import hardwario
from loguru import logger

DEFAULT_LOG_LEVEL = 'DEBUG'
DEFAULT_LOG_FILE = os.path.expanduser("~/.hardwario/console.log")

os.makedirs(os.path.expanduser("~/.hardwario"), exist_ok=True)


@click.group()
@click.option('--log', 'log_level', type=click.Choice(['debug', 'info', 'warning', 'error']), help='Log level', default="warning")
def cli_root(log_level):
    '''HARDWARIO Command Line Tool.'''
    logger.add(sys.stderr, level=log_level.upper())


def main():
    '''Application entry point.'''

    logger.remove()
    logger.add(DEFAULT_LOG_FILE,
               format="{time} | {level} | {name}.{function}: {message}", level="TRACE", rotation="10 MB")

    logger.debug('Argv: {}', sys.argv)

    # discovered and load hardwario cli plugins
    for finder, name, ispkg in pkgutil.iter_modules(hardwario.__path__, hardwario.__name__ + '.'):
        if not ispkg or name == 'hardwario.common':
            continue
        logger.debug('Discovered module: {}', name)
        try:
            module = importlib.import_module(name + '.cli')
            cli_root.add_command(module.cli)
        except Exception as e:
            logger.warning('Module cli import: {}', e)
            if os.getenv('DEBUG', False):
                raise e
            pass

    try:
        cli_root(obj={}, auto_envvar_prefix='HARDWARIO')
    except KeyboardInterrupt:
        pass
    except Exception as e:
        click.secho(str(e), err=True, fg='red')
        if os.getenv('DEBUG', False):
            raise e
        sys.exit(1)
