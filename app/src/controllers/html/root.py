from pathlib import Path

from flask import (Blueprint, current_app, flash, make_response, redirect,
                   render_template, request, url_for)
from flask_babel import lazy_gettext

from app.src import enums, site_data
from app.src.modules import refresher

bp = Blueprint('root',
               __name__,
               url_prefix="/")


@bp.route("/")
def index():
    app_conf = site_data.AppConfiguration()
    if not app_conf.get('url'):
        flash(lazy_gettext('missing_api_err_msg'), enums.FlashCategory.error)

    return render_template("index.jinja",
                           refresh_logs=site_data.RefreshHistory().get(),
                           images=refresher.cached_images(
                               Path(current_app.config['CACHE_DIR']).joinpath('epaper')),
                           app_conf=app_conf)


@bp.route('language/<lang>')
def change_language(lang: str):
    response = make_response(
        redirect(request.referrer or url_for('root.home')))
    response.set_cookie('locale', lang)
    return response
