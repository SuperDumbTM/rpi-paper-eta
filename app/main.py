from logging.config import dictConfig
from pathlib import Path
from typing import Optional

import dotenv
from flask import Flask, current_app, request
from flask_babel import Babel

from app import commands, config, controllers, handles, utils


def init_babel(app: Flask) -> Babel:
    """Initialise babel
    """
    return Babel(app, locale_selector=utils.get_locale)


def init_site_data(app: Flask) -> None:
    """Initialise and load all the site data/user configuration
    """
    config.site_data.RefreshSchedule(app)
    config.site_data.RefreshHistory(limit=20)


def init_logger(app: Flask) -> None:
    # https://flask.palletsprojects.com/en/2.3.x/logging/#basic-configuration
    # https://betterstack.com/community/guides/logging/how-to-start-logging-with-flask/
    dictConfig({
        'version': 1,
        'formatters': {
            'console': {
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
                'formatter': 'console',
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


def create_app() -> Flask:
    app = Flask(__name__, template_folder="template", static_folder="static")

    app.config.from_pyfile(
        Path(__file__).parent / "config" / "flask_config.py")
    app.config.from_mapping(
        dotenv.dotenv_values(app.config.get("ENV_FILE_PATH")))

    app.register_blueprint(controllers.html.configuration.bp)
    app.register_blueprint(controllers.html.schedule.bp)
    app.register_blueprint(controllers.html.root.bp)
    app.register_blueprint(controllers.html.log.bp)

    app.register_blueprint(controllers.apis.config.bp)
    app.register_blueprint(controllers.apis.display.bp)
    app.register_blueprint(controllers.apis.schedule.bp)
    app.register_blueprint(controllers.apis.log.bp)

    app.cli.add_command(commands.i18n_cli)
    app.cli.add_command(commands.clean_cli)

    app.register_blueprint(handles.bp)

    init_jinja_helpers(app)
    init_logger(app)
    init_site_data(app)
    init_babel(app)

    return app


app = create_app()
