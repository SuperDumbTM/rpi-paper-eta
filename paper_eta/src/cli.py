import subprocess
from pathlib import Path

from flask import current_app
from flask.cli import AppGroup

rm_cli = AppGroup('rm', short_help="Remove cache or config files.")
db_cli = AppGroup('db', short_help="Database utilities.")
i18n_cli = AppGroup('i18n', short_help="Translation (Babel) utilities.")


@i18n_cli.command('extract', short_help="Scan for new translations")
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


@i18n_cli.command('update', short_help="Generate the latest .po file")
def babel_update():
    subprocess.run([
        'pybabel',
        'update',
        '-i',
        'messages.pot',
        '-d',
        current_app.config.get('BABEL_TRANSLATION_DIRECTORIES')
    ], check=True)


@i18n_cli.command('modify', short_help="Extract and update")
def babel_extract_update():
    babel_extract()
    babel_update()


@i18n_cli.command('compile')
def babel_compile():
    subprocess.run([
        'pybabel',
        'compile',
        '-d',
        current_app.config.get('BABEL_TRANSLATION_DIRECTORIES')
    ], check=True)


@rm_cli.command('pycache')
def remove_pyc():
    for pyf in Path('.').rglob('*.py[co]'):
        pyf.unlink()
    for pyf in Path('.').rglob('__pycache__'):
        pyf.rmdir()


@rm_cli.command('log')
def remove_log():
    for fname in current_app.config.get('DIR_LOG').glob("*"):
        try:
            Path(fname).unlink()
        except PermissionError:
            with open(Path(fname), 'w', encoding='utf-8'):
                continue


@rm_cli.command('db')
def remove_db():
    print("You are trying to delete the database, all the data will be gone.")
    while (answer := input("Are you sure? [y/N] ")).lower() not in ("y", "yes", "n", "no", ""):
        continue

    if answer in ("n", "no", ""):
        return

    fpath = current_app.config.get('DIR_STORAGE').joinpath("app.db")
    try:
        fpath.unlink()
    except PermissionError:
        with open(fpath, 'w', encoding='utf-8'):
            pass


@rm_cli.command('config')
def remove_config():
    current_app.config.get('PATH_SITE_CONF').unlink(missing_ok=True)
