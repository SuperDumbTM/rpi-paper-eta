import json

from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import lazy_gettext

from app.src import enums, forms, site_data
from app.src.libs import image as eimage

bp = Blueprint('configuration',
               __name__,
               url_prefix="/configuration")


@bp.route('/')
def index():
    app_conf = site_data.AppConfiguration()
    if app_conf.get('epd_brand'):
        models = [m.__name__
                  for m in eimage.eta_image.EtaImageGeneratorFactory.models(app_conf.get('epd_brand'))]
    else:
        models = []

    return render_template("configuration/index.jinja",
                           brands=eimage.eta_image.EtaImageGeneratorFactory.brands(),
                           models=models,
                           app_conf=app_conf)


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
        flash(lazy_gettext('import_failed'), enums.FlashCategory.error)
    return redirect(url_for('configuration.index'))


@bp.route('/epd')
def epaper_setting():
    app_conf = site_data.AppConfiguration()

    if app_conf.get('epd_brand'):
        models = [m.__name__ for m in eimage.eta_image.EtaImageGeneratorFactory.models(
            app_conf.get('epd_model'))]
    else:
        models = []
    return render_template("configuration/epd_form.jinja",
                           brands=eimage.eta_image.EtaImageGeneratorFactory.brands(),
                           models=models,
                           form=forms.EpaperForm(epd_brand=app_conf.get('epd_brand'),
                                                 epd_model=app_conf.get('epd_model')))


@bp.route('/api-server')
def api_server_setting():
    app_conf = site_data.AppConfiguration()
    return render_template("configuration/api_server_form.jinja",
                           form=forms.ApiServerForm(url=app_conf.get('api_url'),
                                                    username=app_conf.get(
                                                        'api_username'),
                                                    password=app_conf.get('api_password'))
                           )
