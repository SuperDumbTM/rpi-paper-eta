from flask import Blueprint, render_template

bp = Blueprint('schedule',
               __name__,
               template_folder="../../templates",
               url_prefix="/schedule")


@bp.route('/')
def schedules():
    return render_template("schedule/schedule_list.jinja")


@bp.route('/create')
def create():
    # passing Python functions to template
    # https://stackoverflow.com/questions/62029141/cant-use-zip-from-jinja2
    return render_template("schedule/schedule_form.jinja", zip=zip, list=list)
