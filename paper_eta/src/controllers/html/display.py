import base64
import io

from flask import Blueprint, current_app, render_template
from PIL import Image

from paper_eta.src.libs import epd_log, refresher

bp = Blueprint('display', __name__, url_prefix="/display")


def _img_2_b64(img: Image.Image) -> str:
    """Convert a PIL image to base64 encoded string."""
    b = io.BytesIO()
    img.save(b, 'bmp')
    return base64.b64encode(b.getvalue()).decode('utf-8')


@bp.route("/screen-dumps")
def screen_dumps():
    return render_template("display/partials/screen_dumps.jinja",
                           images={
                               k: _img_2_b64(v)
                               for k, v in refresher.cached_images(
                                   current_app.config['DIR_SCREEN_DUMP']).items()
                           },)


@bp.route("/histories")
def histories():
    return render_template("display/partials/histories.jinja",
                           refresh_logs=tuple(epd_log.epdlog.get()),)
