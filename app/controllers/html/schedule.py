import json
import logging

from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import lazy_gettext

from app import config, enums, forms
from app.config import site_data
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
    conf = config.site_data.AppConfiguration().confs

    if conf.epd_brand is None or conf.epd_model is None:
        # TODO: handles no epd setting
        return redirect()

    # the template needs zip and list
    # https://stackoverflow.com/questions/62029141/cant-use-zip-from-jinja2
    return render_template("schedule/schedule_form.jinja",
                           zip=zip,
                           list=list,
                           form=forms.ScheduleForm(),
                           form_action=url_for('api_schedule.create'),
                           form_method='post',
                           eta_types=eimage.enums.EtaType,
                           layouts=eimage.eta_image.EtaImageGeneratorFactory.get_generator(
                               conf.epd_brand, conf.epd_model).layouts()
                           )


@bp.route('/create/edit/<id>')
def edit(id: str):
    conf = config.site_data.AppConfiguration().confs
    scheduler = config.site_data.RefreshSchedule()

    # the template needs zip and list
    # https://stackoverflow.com/questions/62029141/cant-use-zip-from-jinja2
    return render_template("schedule/schedule_form.jinja",
                           zip=zip,
                           list=list,
                           form=forms.ScheduleForm(
                               **scheduler.get(id).model_dump(exclude=['id'])),
                           form_action=url_for(
                               'api_schedule.update', id=id),
                           form_method='put',
                           eta_types=eimage.enums.EtaType,
                           layouts=eimage.eta_image.EtaImageGeneratorFactory.get_generator(
                               conf.epd_brand, conf.epd_model).layouts()
                           )


@bp.route('/export')
def export():
    scheduler = config.site_data.RefreshSchedule()
    return Response(
        json.dumps(
            tuple(map(lambda s: s.model_dump(
                exclude=['id', 'enabled']), scheduler.get_all())),
            indent=4),
        mimetype='application/json',
        headers={'Content-disposition': 'attachment; filename=schedule.json'})


@bp.route('/import', methods=['POST'])
def import_():
    try:
        file = request.files['schedule']

        scheduler = site_data.RefreshSchedule()
        for schedule in json.load(file.stream):
            try:
                scheduler.create(schedule['schedule'],
                                 schedule['eta_type'],
                                 schedule['layout'],
                                 schedule['is_partial'],
                                 False)
                # TODO: validation
            except KeyError:
                logging.exception(
                    'Encountering missing field(s) during refresh schedule import.')
                pass
    except (UnicodeDecodeError, json.decoder.JSONDecodeError) as e:
        print(e)
        flash(lazy_gettext('import_failed'), enums.FlashCategory.error)
    return redirect(url_for('schedule.schedules'))
