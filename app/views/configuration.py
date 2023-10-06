from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request)

from app import forms, utils

bp = Blueprint('configuration',
               __name__,
               template_folder="../templates",
               url_prefix="/configuration")


@bp.route('/')
def index():
    return render_template("configuration/index.jinja")


@bp.route('/api-server', methods=['GET', 'POST'])
def api_server():
    form = forms.ApiServerForm()

    if form.is_submitted():
        form.validate()
    return render_template("configuration/api-server.jinja",
                           api_url=current_app.config.get("API_URL"),
                           api_username=current_app.config.get(
                               "API_USERNAME"),
                           api_password=current_app.config.get("API_PASSWORD"),
                           form=form
                           )
