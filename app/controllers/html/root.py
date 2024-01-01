import base64
from pathlib import Path

from flask import Blueprint, flash, redirect, render_template, url_for

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
                           images=refresher.cached_images(
                               Path(config.flask_config.CACHE_DIR).joinpath('epaper')),
                           aconf=aconf)
