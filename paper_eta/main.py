import urllib.parse
from logging.config import dictConfig
from pathlib import Path

from flask import Flask

from .src import cli, controllers, extensions, handles, models, utils


def create_app() -> Flask:
    app_root = Path(__file__).parent
    app = Flask(__name__,
                template_folder=app_root.joinpath('templates'),
                static_folder=app_root.joinpath('static'))

    app.config.from_pyfile(Path(__file__).parent.joinpath('src', 'config.py'))

    # logging configuration
    dictConfig(app.config['LOGGING_CONFIG'])

    # extensions initisation
    extensions.babel.init_app(app, locale_selector=utils.i18n.get_locale)
    extensions.scheduler.init_app(app)
    extensions.scheduler.start()
    extensions.db.init_app(app)
    extensions.hketa.data_path = app.config['HKETA_PATH_DATA']
    extensions.hketa.threshold = app.config['HKETA_THRESHOLD']

    # blueprints registration
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

    # cli registration
    app.cli.add_command(cli.i18n_cli)
    app.cli.add_command(cli.clean_cli)
    app.cli.add_command(cli.db_cli)

    # exception handler registration
    app.register_blueprint(handles.bp)

    # jinja helper functions
    app.jinja_env.globals.update(
        bool_to_icon=lambda b: '<i class="bi bi-check2"></i>' if b else '<i class="bi bi-x"></i>',
        get_locale=utils.i18n.get_locale,
        form_valid_class=lambda f: ' is-invalid' if f.errors else ''
    )
    app.jinja_env.filters.update({
        'unquote': urllib.parse.unquote,
    })

    with app.app_context():
        extensions.db.create_all()
        for s in models.Schedule.query.all():
            if s.enabled:
                s.add_job()
    return app
