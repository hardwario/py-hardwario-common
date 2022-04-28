import os
from pydoc import cli
import sys
import pkgutil
import importlib
import click
from loguru import logger
import hardwario

DEFAULT_LOG_LEVEL = 'DEBUG'
DEFAULT_LOG_FILE = os.path.expanduser("~/.hardwario/cli.log")

os.makedirs(os.path.expanduser("~/.hardwario"), exist_ok=True)


def version_cb(ctx, param, value):
    modules = ctx.obj['modules']
    for name in sorted(modules):
        click.echo(f'{name} {modules[name]}')
    ctx.exit()


@ click.group()
@ click.option('--log-level', type=click.Choice(['debug', 'info', 'success', 'warning', 'error', 'critical']),
               help='Log level to stderr', default="critical", show_default=True)
@ click.option('--version', is_flag=True, expose_value=False, help='Show the version and exit.', callback=version_cb)
def cli_root(log_level):
    '''HARDWARIO Command Line Tool.'''
    logger.add(sys.stderr, level=log_level.upper())


def main():
    '''Application entry point.'''

    logger.remove()
    logger.add(DEFAULT_LOG_FILE,
               format='{time} | {level} | {name}.{function}: {message}',
               level='TRACE',
               rotation='10 MB',
               retention=3)

    logger.debug('Argv: {}', sys.argv)

    modules = {
        'hardwario.common': hardwario.common.__version__
    }

    logger.debug('Module: hardwario.common Version: {}', hardwario.common.__version__)

    # discovered and load hardwario cli plugins
    for finder, name, ispkg in pkgutil.iter_modules(hardwario.__path__, hardwario.__name__ + '.'):
        if not ispkg or name == 'hardwario.common':
            continue
        logger.debug('Discovered module: {}', name)
        try:
            module = importlib.import_module(name)
            # modules[name] = '?'
            if hasattr(module, '__version__'):
                logger.debug('Module: {} version {}', name, module.__version__)
                modules[name] = module.__version__
            if hasattr(module, 'cli'):
                cli_root.add_command(module.cli.cli)
        except Exception as e:
            logger.warning('Module cli import: {}', e)
            if os.getenv('DEBUG', False):
                raise e
            pass

    try:
        cli_root(obj={'modules': modules}, auto_envvar_prefix='HARDWARIO')
    except KeyboardInterrupt:
        pass
    except Exception as e:
        click.secho(str(e), err=True, fg='red')
        if os.getenv('DEBUG', False):
            raise e
        sys.exit(1)
