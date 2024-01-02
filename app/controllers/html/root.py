import base64
from pathlib import Path

from flask import Blueprint, flash, make_response, redirect, render_template, request, session, url_for

from app import config
from app.modules import refresher

bp = Blueprint('root',
               __name__,
               template_folder="../../templates",
               url_prefix="/")


@bp.route("/")
def index():
    aconf = config.site_data.AppConfiguration()
    if not aconf.get('url'):
        flash("Please set the API server URL")
        return redirect(url_for("configuration.api_server_setting"))

    return render_template("index.jinja",
                           refresh_logs=config.site_data.RefreshHistory().get(),
                           images=refresher.cached_images(
                               Path(config.flask_config.CACHE_DIR).joinpath('epaper')),
                           aconf=aconf)


@bp.route('language/<lang>')
def change_language(lang: str):
    response = make_response(
        redirect(request.referrer or url_for('root.home')))
    response.set_cookie('locale', lang)
    return response
