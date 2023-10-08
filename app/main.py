from pathlib import Path

from dotenv import dotenv_values
from flask import Flask, redirect, render_template, url_for

from app.config import site_data
from app import views

app = Flask(__name__, template_folder="template", static_folder="static")

app.config.from_pyfile(Path(__file__).parent / "config" / "flask_config.py")
app.config.from_mapping(dotenv_values(app.config.get("ENV_FILE_PATH")))

app.register_blueprint(views.configuration.bp)
app.register_blueprint(views.schedule.bp)


@app.route("/")
def index():
    if not site_data.ApiServerSetting().url:
        return redirect(url_for("configuration.api_server"))
    return render_template("index.jinja")
