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
    aconf = config.site_data.AppConfiguration()
    if not aconf.get('url'):
        flash("Please set the API server URL")
        return redirect(url_for("configuration.api_server_setting"))

    images = {}
    for path in Path(config.flask_config.CACHE_DIR).joinpath('epaper').glob('**/*'):
        with open(path, 'rb') as f:
            if path.suffix != '.bmp':
                continue
            images[path.name.removesuffix(path.suffix)] = base64.b64encode(
                f.read()).decode("utf-8")

    return render_template("index.jinja", images=images, aconf=aconf)
