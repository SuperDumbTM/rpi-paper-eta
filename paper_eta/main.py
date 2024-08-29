import json
import urllib.parse
from datetime import datetime
from logging.config import dictConfig
from pathlib import Path

from flask import Flask

from paper_eta.src import cli, controllers, database, exts, handles, site_data, utils


def create_app() -> Flask:
    app_root = Path(__file__).parent
    app = Flask(__name__,
                template_folder=app_root.joinpath('templates'),
                static_folder=app_root.joinpath('static'))

    app.config.from_pyfile(Path(__file__).parent.joinpath('src', 'config.py'))

    # logging configuration
    dictConfig(app.config['LOGGING_CONFIG'])

    # extensions initisation
    exts.babel.init_app(app, locale_selector=utils.get_locale)
    exts.scheduler.init_app(app)
    exts.scheduler.start()
    exts.db.init_app(app)
    exts.hketa.data_path = app.config['HKETA_PATH_DATA']
    exts.hketa.threshold = app.config['HKETA_THRESHOLD']

    # blueprints registration
    app.register_blueprint(controllers.bookmark.bp)
    app.register_blueprint(controllers.bookmark_group.bp)
    app.register_blueprint(controllers.configuration.bp)
    app.register_blueprint(controllers.control.bp)
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
        is_dry_run=lambda: site_data.AppConfiguration().get("dry_run", False)
    )
    app.jinja_env.filters.update({
        'unquote': urllib.parse.unquote,
        'tojson': json.dumps
    })

    with app.app_context():
        exts.db.create_all()
        for s in exts.db.session.query(database.Schedule).all():
            try:
                if s.enabled:
                    s.add_job()
            except KeyError:
                # app configuration not exists
                s.enabled = False
        exts.db.session.commit()

    return app
