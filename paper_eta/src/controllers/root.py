from flask import (Blueprint, current_app, flash, make_response, redirect,
                   render_template, request, url_for)
from flask_babel import lazy_gettext

from paper_eta.src import database, site_data, utils
from paper_eta.src.libs import refresher, renderer

bp = Blueprint('root', __name__, url_prefix="/")


@bp.route("/")
def index():
    if not (app_conf := site_data.AppConfiguration()).configurated():
        flash(lazy_gettext("missing_app_config"), "info")
    return render_template("index.jinja", app_conf=app_conf)


@bp.route('language/<lang>')
def change_language(lang: str):
    response = make_response(
        redirect(request.referrer or url_for('root.home')))
    response.set_cookie('locale', lang)
    return response


@bp.route("/screen-dumps")
def screen_dumps():
    return render_template("root/partials/screen_dumps.jinja",
                           image=utils.img2b64(renderer.merge(
                               refresher.load_images(current_app.config['DIR_SCREEN_DUMP']))
                           ))


@bp.route("/histories")
def histories():
    return render_template("root/partials/histories.jinja",
                           refresh_logs=(database.RefreshLog.query
                                         .order_by(database.RefreshLog.created_at.desc())
                                         .all())
                           )
