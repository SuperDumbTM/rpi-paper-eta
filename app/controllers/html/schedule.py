from flask import Blueprint, render_template

bp = Blueprint('schedule',
               __name__,
               template_folder="../../templates",
               url_prefix="/schedule")


@bp.route('/')
def index():
    return render_template("schedule/index.jinja")
