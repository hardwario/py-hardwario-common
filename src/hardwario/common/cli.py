import os
import sys
import logging
import pkgutil
import importlib
import click
import hardwario


@click.group()
@click.option('--log', 'log_level', type=click.Choice(['debug', 'info', 'warning', 'error']), help='Log level', default="warning")
def cli_root(log_level):
    '''HARDWARIO Command Line Tool.'''
    logging.getLogger().setLevel(log_level.upper())


def main():
    '''Application entry point.'''
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(name)s: %(message)s')

    # discovered and load hardwario cli plugins
    for finder, name, ispkg in pkgutil.iter_modules(hardwario.__path__, hardwario.__name__ + '.'):
        if not ispkg or name == 'hardwario.common':
            continue
        try:
            module = importlib.import_module(name + '.cli')
            cli_root.add_command(module.cli)
        except Exception as e:
            if os.getenv('DEBUG', False):
                raise e
            pass

    try:
        cli_root(obj={})
    except KeyboardInterrupt:
        pass
    except Exception as e:
        click.secho(str(e), err=True, fg='red')
        if os.getenv('DEBUG', False):
            raise e
        sys.exit(1)
