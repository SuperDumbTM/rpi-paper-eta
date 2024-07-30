from flask import (Blueprint, current_app, make_response, redirect,
                   render_template, request, url_for)

from ...src import site_data, utils
from ...src.libs import epd_log
from ..libs import epd_log, refresher

bp = Blueprint('root', __name__, url_prefix="/")


@bp.route("/")
def index():
    app_conf = site_data.AppConfiguration()
    return render_template("index.jinja",
                           refresh_logs=tuple(epd_log.epdlog.get()),
                           app_conf=app_conf)


@bp.route('language/<lang>')
def change_language(lang: str):
    response = make_response(
        redirect(request.referrer or url_for('root.home')))
    response.set_cookie('locale', lang)
    return response


@bp.route("/screen-dumps")
def screen_dumps():
    return render_template("root/partials/screen_dumps.jinja",
                           images={
                               k: utils.img2b64(v)
                               for k, v in refresher.cached_images(
                                   current_app.config['DIR_SCREEN_DUMP']).items()
                           },)


@bp.route("/histories")
def histories():
    return render_template("root/partials/histories.jinja",
                           refresh_logs=tuple(epd_log.epdlog.get()),)
