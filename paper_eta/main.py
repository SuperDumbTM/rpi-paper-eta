import json
import urllib.parse
from datetime import datetime
from logging.config import dictConfig
from pathlib import Path

from flask import Flask

from paper_eta.src import cli, controllers, database, extensions, handles, utils


def create_app() -> Flask:
    app_root = Path(__file__).parent
    app = Flask(__name__,
                template_folder=app_root.joinpath('templates'),
                static_folder=app_root.joinpath('static'))

    app.config.from_pyfile(Path(__file__).parent.joinpath('src', 'config.py'))

    # logging configuration
    dictConfig(app.config['LOGGING_CONFIG'])

    # extensions initisation
    extensions.babel.init_app(app, locale_selector=utils.get_locale)
    extensions.scheduler.init_app(app)
    extensions.scheduler.start()
    extensions.db.init_app(app)
    extensions.hketa.data_path = app.config['HKETA_PATH_DATA']
    extensions.hketa.threshold = app.config['HKETA_THRESHOLD']

    # blueprints registration
    app.register_blueprint(controllers.bookmark.bp)
    app.register_blueprint(controllers.configuration.bp)
    app.register_blueprint(controllers.display.bp)
    app.register_blueprint(controllers.schedule.bp)
    app.register_blueprint(controllers.root.bp)
    app.register_blueprint(controllers.log.bp)

    # cli registration
    app.cli.add_command(cli.i18n_cli)
    app.cli.add_command(cli.rm_cli)
    app.cli.add_command(cli.db_cli)

    # exception handler registration
    app.register_blueprint(handles.bp)

    # jinja helper functions
    app.jinja_env.globals.update(
        bool_to_icon=lambda b: '<i class="bi bi-check2"></i>' if b else '<i class="bi bi-x"></i>',
        get_locale=utils.get_locale,
        form_valid_class=lambda f: ' is-invalid' if f.errors else '',
        today=lambda: datetime.now().date(),
        time=lambda: datetime.now().strftime("%H:%M:%S"),
        now=lambda: datetime.now().isoformat(sep=" ", timespec="seconds"),
    )
    app.jinja_env.filters.update({
        'unquote': urllib.parse.unquote,
        'tojson': json.dumps
    })

    with app.app_context():
        extensions.db.create_all()
        for s in extensions.db.session.query(database.Schedule).all():
            try:
                if s.enabled:
                    s.add_job()
            except KeyError:
                # app configuration not exists
                s.enabled = False
        extensions.db.session.commit()
    return app
