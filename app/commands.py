import subprocess
import click
from flask.cli import AppGroup

translation_cli = AppGroup('translation')


@translation_cli.command('extract')
def babel_extract():
    subprocess.run(['pybabel', 'extract', '-F', 'babel.cfg',
                   '-k', 'lazy_gettext', '-o', 'messages.pot', '.'])


@translation_cli.command('update')
def babel_update():
    subprocess.run(['pybabel', 'update', '-i',
                   'messages.pot', '-d', 'translations'])


@translation_cli.command('compile')
def babel_compile():
    subprocess.run(['pybabel', 'compile', '-d', 'translations'])
