import json

from flask import Blueprint, Response, flash, redirect, render_template, url_for
from flask_babel import gettext

from paper_eta.src import site_data
from paper_eta.src.libs import epdcon, refresher

bp = Blueprint('control', __name__, url_prefix="/control")


@bp.route('/', methods=["GET", "POST"])
def index():
    if not site_data.AppConfiguration().configurated():
        flash(gettext("missing_app_config"), "error")
        return redirect(url_for("configuration.index"))
    return render_template("control/index.jinja")


@bp.route("/action/<action>", methods=["POST"])
def do_action(action: str):
    action = action.lower()
    app_conf = site_data.AppConfiguration()

    if (action == "clear-screen"):
        if not app_conf['dry_run']:
            refresher.clear_screen(epdcon.get(app_conf['epd_brand'],
                                              app_conf['epd_model'],
                                              is_partial=False))
        return Response("",
                        status=200,
                        headers={
                            "HX-Trigger": json.dumps({
                                "toast": {
                                    "level": "success",
                                    "message": gettext("success")
                                }
                            })
                        })
