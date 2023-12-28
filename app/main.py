import logging
from logging.config import dictConfig
from pathlib import Path

import dotenv
from flask import Flask, request
from flask.logging import default_handler
from flask_babel import Babel

from app import config, controllers, handles


def init_babel(app: Flask):
    """Initialise babel
    """
    def get_locale():
        crrt_locale = request.cookies.get(
            'locale') or request.headers.get("X-Locale")

        translations = [str(translation)
                        for translation in babel.list_translations()]
        if crrt_locale in translations:
            return crrt_locale

        return request.accept_languages.best_match(translations)
    babel = Babel(app, locale_selector=get_locale)


def init_site_data(app: Flask):
    """Initialise and load all the site data/user configuration
    """
    config.site_data.RefreshSchedule(app)


def init_logger(app: Flask):
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


def create_app():
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

    app.register_blueprint(handles.bp)

    init_logger(app)
    init_site_data(app)
    init_babel(app)

    logging.debug('debug')
    logging.info('info')
    logging.warn('warn')
    logging.error('error')
    logging.critical('critial')

    return app


app = create_app()
