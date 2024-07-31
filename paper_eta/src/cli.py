import subprocess
from pathlib import Path

from flask import current_app
from flask.cli import AppGroup

rm_cli = AppGroup('rm', short_help="Remove cache or config files.")
db_cli = AppGroup('db', short_help="Database utilities.")
i18n_cli = AppGroup('i18n', short_help="Translation (Babel) utilities.")


@i18n_cli.command('extract')
def babel_extract():
    subprocess.run(['pybabel',
                    'extract',
                    '-F',
                    'babel.cfg',
                   '-k',
                    'lazy_gettext',
                    '-o',
                    'messages.pot',
                    '.'], check=True)


@i18n_cli.command('update')
def babel_update():
    subprocess.run([
        'pybabel',
        'update',
        '-i',
        'messages.pot',
        '-d',
        current_app.config.get('BABEL_TRANSLATION_DIRECTORIES')
    ], check=True)


@i18n_cli.command('compile')
def babel_compile():
    subprocess.run([
        'pybabel',
        'compile',
        '-d',
        current_app.config.get('BABEL_TRANSLATION_DIRECTORIES')
    ], check=True)


@rm_cli.command('pycache')
def clean_pyc():
    for pyf in Path('.').rglob('*.py[co]'):
        pyf.unlink()
    for pyf in Path('.').rglob('__pycache__'):
        pyf.rmdir()


@rm_cli.command('log')
def clean_log():
    for fname in current_app.config.get('DIR_LOG').glob("*"):
        try:
            Path(fname).unlink()
        except PermissionError:
            with open(Path(fname), 'w', encoding='utf-8'):
                continue
