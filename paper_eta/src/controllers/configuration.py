import json

from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import gettext, lazy_gettext

from paper_eta.src import database, db, forms, site_data
from paper_eta.src.libs import epdcon

bp = Blueprint('configuration', __name__, url_prefix="/configuration")


@bp.route('/', methods=["GET", "POST"])
def index():
    app_conf = site_data.AppConfiguration()
    form = forms.EpaperSettingForm(**{k: v for k, v in app_conf.items()})

    if form.validate_on_submit():
        if (app_conf.get('epd_brand') != form.epd_brand.data
                or app_conf.get('epd_model') != form.epd_model.data):
            # changing brand or model will invalidate the schedule
            database.Schedule.query.update({database.Schedule.enabled: False})
            flash(gettext("schedule_disabled_message"), "info")
        database.Bookmark.query.update({"locale": form.eta_locale.data})
        db.session.commit()

        try:
            app_conf.updates({k: v for k, v in form.data.items()
                             if k not in ("csrf_token", "submit")})
            return redirect(request.referrer)
        except KeyError:
            return redirect(request.referrer)

    if app_conf.get('epd_brand'):
        form.epd_model.choices = [(m, m) for m in
                                  epdcon.models(app_conf["epd_brand"])]

    return render_template("configuration/index.jinja",
                           form=form,
                           brands=epdcon.brands())


@bp.route('/epd-models/<brand>')
def epd_models(brand: str):
    app_conf = site_data.AppConfiguration()
    try:
        return render_template("configuration/partials/model_options.jinja",
                               current=app_conf.get('epd_model'),
                               models=tuple(epdcon.models(brand)))
    except KeyError:
        return render_template("configuration/partials/model_options.jinja",
                               models=[])


@bp.route('/export')
def export():
    app_conf = site_data.AppConfiguration()
    return Response(
        json.dumps(dict(app_conf), indent=4),
        mimetype='application/json',
        headers={'Content-disposition': 'attachment; filename=paper-eta-config.json'})


@bp.route('/import', methods=['POST'])
def import_():
    file = request.files.get('configurations')
    app_conf = site_data.AppConfiguration()

    try:
        if file:
            app_conf.updates(json.load(file))
    except TypeError:
        flash(lazy_gettext('import_failed'), "error")
    return redirect(url_for('configuration.index'))
