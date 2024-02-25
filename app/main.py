import random
import shutil
import string
import subprocess
from logging.config import dictConfig
from pathlib import Path

import dotenv
from flask import Flask
from flask_babel import Babel

from app.src import commands, controllers, handles, site_data, utils, database


def init_babel(app: Flask) -> Babel:
    """Initialise babel
    """
    app.logger.info("Compiling the translation files.")
    subprocess.run(['pybabel', 'compile', '-d', 'app/translations'])
    return Babel(app, locale_selector=utils.get_locale)


def init_site_data(app: Flask) -> None:
    """Initialise and load all the site data/user configuration
    """
    site_data.RefreshHistory()


def init_logger(app: Flask) -> None:
    # https://flask.palletsprojects.com/en/2.3.x/logging/#basic-configuration
    # https://betterstack.com/community/guides/logging/how-to-start-logging-with-flask/
    # https://gist.github.com/deepaksood619/99e790959f5eba6ba0815e056a8067d7
    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'print': {
                'format': '[%(levelname)s] %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
            'detailed': {
                'format': '[%(asctime)s][%(levelname)s][%(name)s.%(module)s]: %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
        },
        'handlers': {
            'wsgi': {
                'level': 'DEBUG' if app.debug else 'INFO',
                'class': 'logging.StreamHandler',
                'stream': 'ext://flask.logging.wsgi_errors_stream',
                'formatter': 'print',
            },
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "print",
                "stream": "ext://sys.stdout",
            },
            'size-rotate': {
                'level': 'DEBUG',
                "class": "logging.handlers.RotatingFileHandler",
                "maxBytes": 3145728,
                "filename": app.config['LOG_FILE_PATH'],
                'encoding': 'utf-8',
                "formatter": "detailed",
            },
        },
        'loggers': {
            "gunicorn.error": {
                "handlers": ['console', 'size-rotate'],
                "level": "INFO",
                "propagate": False,
            },
            "gunicorn.access": {
                "handlers": ["console"] if app.debug else ['console', 'size-rotate'],
                "level": "DEBUG",
                "propagate": False,
            },
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['wsgi', 'size-rotate']
        },
    })


def init_jinja_helpers(app: Flask) -> None:
    app.jinja_env.globals.update(
        bool_to_icon=lambda b: '<i class="bi bi-check2"></i>' if b else '<i class="bi bi-x"></i>',
        get_locale=utils.get_locale,
    )


def init_db(app: Flask) -> None:
    database.db.init_app(app)

    database.scheduler.init_app(app)
    database.scheduler.start()

    with app.app_context():
        database.db.create_all()

        for s in database.db.session.query(database.Schedule).all():
            if s.enabled:
                s.add_job()


def create_app() -> Flask:
    app_root = Path(__file__).parent
    app = Flask(__name__,
                template_folder=app_root.joinpath('templates'),
                static_folder=app_root.joinpath('static'))

    env_file_path = Path(__file__).parent.parent.joinpath('.env')
    # .env file initialisation
    if not env_file_path.exists():
        shutil.copy(f'{env_file_path.name}.sample', env_file_path)
        dotenv.set_key(env_file_path,
                       'SECRET_KEY',
                       ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                               for _ in range(64)))

    app.config.from_mapping({
        'DATA_DIR': app_root.joinpath("data"),
        'CACHE_DIR': app_root.joinpath("caches"),
        'EPD_IMG_DIR': app_root.joinpath("caches", 'epaper'),
        'LOG_FILE_PATH': app_root.joinpath("logs", 'app.log'),
        'I18N': ['en', 'zh_Hant_HK'],
        'BABEL_TRANSLATION_DIRECTORIES': str(app_root.joinpath("translations")),
        'SQLALCHEMY_DATABASE_URI': "sqlite:///{}".format(app_root.joinpath('data', 'app.db'))
    })
    app.config.from_mapping(dotenv.dotenv_values('./.env'))

    app.register_blueprint(controllers.html.bookmark.bp)
    app.register_blueprint(controllers.html.configuration.bp)
    app.register_blueprint(controllers.html.schedule.bp)
    app.register_blueprint(controllers.html.root.bp)
    app.register_blueprint(controllers.html.log.bp)

    app.register_blueprint(controllers.apis.config.bp)
    app.register_blueprint(controllers.apis.display.bp)
    app.register_blueprint(controllers.apis.schedule.bp)
    app.register_blueprint(controllers.apis.log.bp)
    app.register_blueprint(controllers.apis.bookmark.bp)

    app.cli.add_command(commands.i18n_cli)
    app.cli.add_command(commands.clean_cli)

    app.register_blueprint(handles.bp)

    init_db(app)
    init_jinja_helpers(app)
    init_logger(app)
    init_site_data(app)
    init_babel(app)

    return app
