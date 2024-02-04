import subprocess
from pathlib import Path

from flask.cli import AppGroup

i18n_cli = AppGroup('i18n')
clean_cli = AppGroup('clean')


@i18n_cli.command('extract')
def babel_extract():
    subprocess.run(['pybabel', 'extract', '-F', 'babel.cfg',
                   '-k', 'lazy_gettext', '-o', 'messages.pot', '.'])


@i18n_cli.command('update')
def babel_update():
    subprocess.run(['pybabel', 'update', '-i',
                   'messages.pot', '-d', 'app/translations'])


@i18n_cli.command('compile')
def babel_compile():
    subprocess.run(['pybabel', 'compile', '-d', 'app/translations'])


@clean_cli.command('pycache')
def clean_pyc():
    for pyf in Path('.').rglob('*.py[co]'):
        pyf.unlink()
    for pyf in Path('.').rglob('__pycache__'):
        pyf.rmdir()
