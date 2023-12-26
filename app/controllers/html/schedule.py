from flask import Blueprint, redirect, render_template, url_for
from app import config, forms

from app.modules import image as eimage


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
                           form=forms.ScheduleForm(),
                           form_action=url_for('api_schedule.create_schedule'),
                           form_method='post',
                           eta_types=eimage.enums.EtaType,
                           layouts=eimage.eta_image.EtaImageGeneratorFactory.get_generator(
                               epd.brand, epd.model).layouts()
                           )


@bp.route('/create/edit/<id>')
def edit(id: str):
    epd = config.site_data.EpaperSetting()
    scheduler = config.site_data.RefreshSchedule()

    # the template needs zip and list
    # https://stackoverflow.com/questions/62029141/cant-use-zip-from-jinja2
    return render_template("schedule/schedule_form.jinja",
                           zip=zip,
                           list=list,
                           form=forms.ScheduleForm(
                               **scheduler.get(id).model_dump(exclude=['id'])),
                           form_action=url_for(
                               'api_schedule.update_schedule', id=id),
                           form_method='put',
                           eta_types=eimage.enums.EtaType,
                           layouts=eimage.eta_image.EtaImageGeneratorFactory.get_generator(
                               epd.brand, epd.model).layouts()
                           )
