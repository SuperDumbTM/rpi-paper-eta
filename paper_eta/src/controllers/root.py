from flask import (Blueprint, current_app, flash, make_response, redirect,
                   render_template, request, url_for)
from flask_babel import lazy_gettext

from paper_eta.src import extensions, site_data, utils
from paper_eta.src.libs import epd_log, refresher

bp = Blueprint('root', __name__, url_prefix="/")


@bp.route("/")
def index():
    if not (app_conf := site_data.AppConfiguration()).configurated():
        flash(lazy_gettext("missing_app_config"), "info")
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
                               for k, v in extensions.imgen.load().items()
                           },)


@bp.route("/histories")
def histories():
    return render_template("root/partials/histories.jinja",
                           refresh_logs=tuple(epd_log.epdlog.get()),)


@bp.route("/hti")
def test():

    from paper_eta.src.libs import hketa
    from paper_eta.src import database, extensions
    from paper_eta.src.libs import renderer

    bookmarks = [hketa.RouteQuery(**bm.as_dict())
                 for bm in database.Bookmark.query
                 .filter(database.Bookmark.enabled)
                 .order_by(database.Bookmark.ordering)
                 .all()]

    etas = []
    for bm in bookmarks:
        etap = extensions.hketa.create_eta_processor(bm)
        etas.append(etap.etas())

    try:
        r = renderer.Renderer(current_app)
        print(r.render("waveshare", "epd3in7", "mixed", "6_row_2_eta", etas))
    except Exception as e:
        print(e)

    return render_template("epaper/waveshare/epd3in7/mixed/6_row_2_eta.jinja",
                           etas=etas,
                           display="mixed")
