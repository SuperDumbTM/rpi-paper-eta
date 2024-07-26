import json
import logging
from datetime import datetime
from http import HTTPStatus

import croniter
import sqlalchemy.exc
from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import gettext, lazy_gettext

from paper_eta.src import forms

from ....src import db, enums, models, site_data
from ...libs import eta_img

bp = Blueprint('schedule',
               __name__,
               template_folder="../../../templates",
               url_prefix="/")


@bp.route('/schedules')
def index():
    if request.headers.get('HX-Request'):
        schedules = []
        for schedule in models.Schedule.query.all():
            schedule: models.Schedule

            cron = croniter.croniter(
                schedule.schedule, start_time=datetime.now())

            # TODO: i18n for eta_mode
            schedules.append({
                **dict(schedule.as_dict()),
                'next_execution': (lazy_gettext("not_enabled")
                                   if not schedule.enabled
                                   else cron.get_next(datetime).isoformat())
            })
        return Response(render_template("schedule/partials/rows.jinja", schedules=schedules),
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    return render_template("schedule/index.jinja")


@ bp.route('/create', methods=["GET", "POST"])
def create():
    app_conf = site_data.AppConfiguration()
    if not app_conf.get('epd_brand') or not app_conf.get('epd_model'):
        flash(lazy_gettext("Please enter the display details first."),
              enums.FlashCategory.error)
        return redirect(url_for('configuration.index'))

    form = forms.ScheduleForm()

    if form.validate_on_submit():
        db.session.add(models.Schedule(**{k: v for k, v in form.data.items()
                                          if k not in ("csrf_token", "submit")}))
        db.session.commit()
        return redirect(url_for("schedule.index"))

    return render_template("schedule/form.jinja",
                           zip=zip,
                           list=list,
                           form=form,
                           formats=[c[0] for c in form.eta_format.choices],
                           )


@bp.route('/schedule/create/edit/<id>', methods=["GET", "POST"])
def edit(id: str):
    form = forms.ScheduleForm()
    sch = models.Schedule.query.get_or_404(id)

    if form.validate_on_submit():
        for k, v in form.data.items():
            setattr(sch, k, v)
        db.session.merge(sch)
        db.session.commit()
        return redirect(url_for("schedule.index"))

    form.schedule.data = sch.schedule
    form.eta_format.data = sch.eta_format
    form.layout.data = sch.layout
    form.is_partial.data = sch.is_partial
    form.enabled.data = sch.enabled

    return render_template("schedule/form.jinja",
                           zip=zip,
                           list=list,
                           form=form,
                           formats=[c[0] for c in form.eta_format.choices],
                           )


@bp.route('/schdeule/status/<id>', methods=["PUT"])
def update_status(id: str):
    try:
        schedule = models.Schedule.query.get(id)
        setattr(schedule, "enabled", not schedule.enabled)
        db.session.commit()
        return Response(
            headers={
                "HX-Location": json.dumps({
                    "path": url_for("schedule.index"),
                    "target": "tbody",
                    "swap": "innerHTML"
                })}
        )
    except sqlalchemy.exc.SQLAlchemyError:
        return Response(
            "",
            headers={
                "HX-Reswap": "outterHTML",
                "HX-Retarget": ""
            })


@bp.route('/schedule/<string:id>', methods=["DELETE"])
def delete(id: str):
    try:
        schedule = models.Schedule.query.get(id)
        db.session.delete(schedule)
        db.session.commit()
        return Response(
            headers={
                "HX-Location": json.dumps({
                    "path": url_for("schedule.index"),
                    "target": "tbody",
                    "swap": "innerHTML"
                })}
        )
    except sqlalchemy.exc.SQLAlchemyError:
        return Response(
            "",
            headers={
                "HX-Reswap": "outterHTML",
                "HX-Retarget": ""
            })


@bp.route("/schedule/layouts/<eta_format>")
def layouts(eta_format: str):
    app_conf = site_data.AppConfiguration()
    if not app_conf.get('epd_brand') or not app_conf.get('epd_model'):
        return Response(render_template("/schedule/partials/layout_radio.jinja",
                                        layouts=[],
                                        eta_format=eta_format),
                        headers={"HX-Trigger": json.dumps({
                            "toast": {
                                "level": "error",
                                "message": gettext("Please enter the display details first.")
                            }
                        })})

    try:
        layouts = eta_img.generator.EtaImageGeneratorFactory\
            .get_generator(app_conf.get('epd_brand'), app_conf.get('epd_model'))\
            .layouts()[eta_format]

        return render_template("/schedule/partials/layout_radio.jinja",
                               layouts=layouts,
                               eta_format=eta_format)
    except KeyError:
        return Response(render_template("/schedule/partials/layout_radio.jinja",
                                        layouts=[],
                                        eta_format=eta_format),
                        headers={"HX-Trigger": json.dumps({
                            "toast": {
                                "level": "error",
                                "message": gettext("Layout does not exists.")
                            }
                        })})


@ bp.route('/schedule/export')
def export():
    return Response(
        json.dumps(
            tuple(map(lambda s: s.as_dict(exclude=['id', 'enabled']),
                      models.Schedule.query.all())
                  ),
            indent=4),
        mimetype='application/json',
        headers={'Content-disposition': 'attachment; filename=schedules.json'})


@ bp.route('/schedule/import', methods=['POST'])
def import_():
    fields = ({c.name for c in models.Schedule.__table__.c} -
              {'id', 'enabled', 'created_at', 'updated_at'})  # accepted fields for table inputs
    try:
        for i, schedule in enumerate(json.load(request.files['schedules'].stream)):
            # reference: https://stackoverflow.com/a/76799290
            with db.session.begin_nested() as session:
                try:
                    db.session.add(
                        models.Schedule(**{**{k: schedule[k] for k in fields}, 'enabled': False}))
                    db.session.flush()
                except (KeyError, TypeError, sqlalchemy.exc.StatementError):
                    session.rollback()

                    flash(lazy_gettext('Failed to import no. %(entry)s schedule.', entry=i),
                          enums.FlashCategory.error)
                    logging.exception('Encountering missing field(s) or invalid '
                                      'values during refresh schedule import.')
        db.session.commit()
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        flash(lazy_gettext('import_failed'), enums.FlashCategory.error)
    return redirect(url_for('schedule.index'))
