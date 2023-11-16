from pathlib import Path

from dotenv import dotenv_values
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_babel import Babel

from app.config import site_data
from app import controllers, enums


# flask app initialisation
app = Flask(__name__, template_folder="template", static_folder="static")

app.config.from_pyfile(Path(__file__).parent / "config" / "flask_config.py")
app.config.from_mapping(dotenv_values(app.config.get("ENV_FILE_PATH")))

app.register_blueprint(controllers.configuration.bp)
app.register_blueprint(controllers.schedule.bp)

app.register_blueprint(controllers.apis.config.bp)
app.register_blueprint(controllers.apis.display.bp)

# babel initialisation


def get_locale():
    crrt_locale = request.cookies.get(
        'locale') or request.headers.get("X-Locle")
    translations = [str(translation)
                    for translation in babel.list_translations()]
    if crrt_locale in translations:
        return crrt_locale
    return request.accept_languages.best_match(translations)


babel = Babel(app, locale_selector=get_locale)


@app.route("/")
def index():
    if not site_data.ApiServerSetting().url:
        flash("Please set the API server URL")
        return redirect(url_for("configuration.api_server"))
    return render_template("index.jinja")
