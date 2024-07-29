import base64
import io

from flask import (Blueprint, make_response, redirect, render_template,
                   request, url_for)
from PIL import Image

from ...src import site_data
from ...src.libs import epd_log

bp = Blueprint('root', __name__, url_prefix="/")


def _img_2_b64(img: Image.Image) -> str:
    """Convert a PIL image to base64 encoded string."""
    b = io.BytesIO()
    img.save(b, 'bmp')
    return base64.b64encode(b.getvalue()).decode('utf-8')


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
