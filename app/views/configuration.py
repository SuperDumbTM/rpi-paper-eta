from flask import Blueprint, current_app, flash, redirect, render_template

from app import utils

bp = Blueprint('configuration',
               __name__,
               template_folder="../templates",
               url_prefix="/configuration")


@bp.route('/')
def index():
    return render_template("configuration/index.html")


@bp.route('/api-server')
def api_server():
    return render_template("configuration/api-server.html",
                           api_url=current_app.config.get("API_URL"),
                           api_username=current_app.config.get(
                               "API_USERNAME"),
                           api_password=current_app.config.get("API_PASSWORD")
                           )


@bp.route('/api-server', methods=['POST'])
def api_server_submit():
    flash('flash 1')
    flash('flash 2')
    return redirect(utils.redirect_url())
