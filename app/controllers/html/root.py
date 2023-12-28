import base64
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, url_for

from app import config

bp = Blueprint('root',
               __name__,
               template_folder="../../templates",
               url_prefix="/")


@bp.route("/")
def index():
    if not config.site_data.ApiServerSetting().url:
        flash("Please set the API server URL")
        return redirect(url_for("configuration.api_server_setting"))

    images = {}
    for path in Path(config.flask_config.CACHE_DIR).joinpath('epaper').glob('**/*'):
        with open(path, 'rb') as f:
            if path.suffix != '.bmp':
                continue
            images[path.name.removesuffix(path.suffix)] = base64.b64encode(
                f.read()).decode("utf-8")

    epd = config.site_data.EpaperSetting()

    return render_template("index.jinja", images=images, epd=epd)
