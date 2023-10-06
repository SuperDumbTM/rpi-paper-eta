import os
from pathlib import Path

from dotenv import dotenv_values
from flask import Flask, redirect, render_template, url_for

from app.views import configuration, schedule

app = Flask(__name__, template_folder="template", static_folder="static")

app.config.from_pyfile(Path(__file__).parent / "config.py")
app.config.from_mapping(dotenv_values(app.config.get("ENV_FILE_PATH")))

app.register_blueprint(configuration.bp)
app.register_blueprint(schedule.bp)


@app.route("/")
def index():
    if not app.config.get("API_URL"):
        return redirect(url_for("configuration.index"))
    return render_template("index.html")
