import base64
import io

from flask import (Blueprint, current_app, flash, make_response, redirect,
                   render_template, request, url_for)
from flask_babel import lazy_gettext
from PIL import Image

from app.src import enums, site_data
from app.src.libs import refresher

bp = Blueprint('root', __name__, url_prefix="/")


def _img_2_b64(img: Image.Image) -> str:
    """Convert a PIL image to base64 encoded string."""
    b = io.BytesIO()
    img.save(b, 'bmp')
    return base64.b64encode(b.getvalue()).decode('utf-8')


@bp.route("/")
def index():
    app_conf = site_data.AppConfiguration()
    if not app_conf.get('api_url'):
        flash(lazy_gettext('missing_api_err_msg'), enums.FlashCategory.error)

    return render_template("index.jinja",
                           refresh_logs=tuple(
                               site_data.RefreshHistory().get()),
                           images={
                               k: _img_2_b64(v)
                               for k, v in refresher.cached_images(
                                   current_app.config['CACHE_DIR'].joinpath('epaper')).items()
                           },
                           app_conf=app_conf)


@bp.route('language/<lang>')
def change_language(lang: str):
    response = make_response(
        redirect(request.referrer or url_for('root.home')))
    response.set_cookie('locale', lang)
    return response
