from flask import Blueprint, redirect, render_template
from app import config

from app.modules.image.eta_image import EtaImageGeneratorFactory


bp = Blueprint('schedule',
               __name__,
               template_folder="../../templates",
               url_prefix="/schedule")


@bp.route('/')
def schedules():
    return render_template("schedule/schedule_list.jinja")


@bp.route('/create')
def create():
    epd = config.site_data.EpaperSetting()

    if epd.brand is None or epd.model is None:
        # TODO: handles no epd setting
        return redirect()

    # the template needs zip and list
    # https://stackoverflow.com/questions/62029141/cant-use-zip-from-jinja2
    return render_template("schedule/schedule_form.jinja",
                           zip=zip,
                           list=list,
                           layouts=EtaImageGeneratorFactory.get_generator(
                               epd.brand, epd.model).layouts()
                           )
