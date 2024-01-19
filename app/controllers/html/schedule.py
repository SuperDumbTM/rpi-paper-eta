import json
import logging

from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import lazy_gettext
from sqlalchemy.exc import StatementError

from app import database, site_data, enums, forms
from app import site_data
from app.modules import image as eimage

bp = Blueprint('schedule',
               __name__,
               template_folder="../../templates",
               url_prefix="/schedule")


@bp.route('/schedules')
def index():
    return render_template("schedule/list.jinja")


@bp.route('/create')
def create():
    app_conf = site_data.AppConfiguration()

    if not app_conf.get('epd_brand') or not app_conf.get('epd_model'):
        # TODO: handles no epd setting
        return redirect()

    # the template needs zip and list
    # https://stackoverflow.com/questions/62029141/cant-use-zip-from-jinja2
    return render_template("schedule/form.jinja",
                           zip=zip,
                           list=list,
                           schedule=database.Schedule(),
                           form_action=url_for('api_schedule.create'),
                           form_method='post',
                           eta_types=eimage.enums.EtaType,
                           layouts=eimage.eta_image.EtaImageGeneratorFactory.get_generator(
                               app_conf.get('epd_brand'), app_conf.get('epd_model')).layouts()
                           )


@bp.route('/schedule/create/edit/<id>')
def edit(id: str):
    app_conf = site_data.AppConfiguration()
    # the template needs zip and list
    # https://stackoverflow.com/questions/62029141/cant-use-zip-from-jinja2
    return render_template("schedule/form.jinja",
                           zip=zip,
                           list=list,
                           schedule=database.Schedule.query.get_or_404(id),
                           form_action=url_for('api_schedule.update', id=id),
                           form_method='put',
                           eta_types=eimage.enums.EtaType,
                           layouts=eimage.eta_image.EtaImageGeneratorFactory.get_generator(
                               app_conf.get('epd_brand'), app_conf.get('epd_model')).layouts()
                           )


@bp.route('/schedule/export')
def export():
    return Response(
        json.dumps(
            tuple(map(lambda s: s.as_dict(exclude=['id', 'enabled']),
                      database.Schedule.query.all())
                  ),
            indent=4),
        mimetype='application/json',
        headers={'Content-disposition': 'attachment; filename=schedules.json'})


@bp.route('/schedule/import', methods=['POST'])
def import_():
    fields = ({c.name for c in database.Schedule.__table__.c} -
              {'id', 'enabled', 'created_at', 'updated_at'})  # accepted fields for table inputs
    try:
        for i, schedule in enumerate(json.load(request.files['schedules'].stream)):
            # reference: https://stackoverflow.com/a/76799290
            with database.db.session.begin_nested() as session:
                try:
                    database.db.session.add(
                        database.Schedule(**{**{k: schedule[k] for k in fields}, 'enabled': False}))
                    database.db.session.flush()
                except (KeyError, TypeError, StatementError):
                    session.rollback()

                    flash(lazy_gettext('Failed to import no. %(entry)s schedule.', entry=i),
                          enums.FlashCategory.error)
                    logging.exception('Encountering missing field(s) or invalid '
                                      'values during refresh schedule import.')
        database.db.session.commit()
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        flash(lazy_gettext('import_failed'), enums.FlashCategory.error)
    return redirect(url_for('schedule.index'))
