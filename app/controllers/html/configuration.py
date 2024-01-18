import json

import pydantic
from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import lazy_gettext

from app import config, enums, forms, models
from app.modules import image as eimage

bp = Blueprint('configuration',
               __name__,
               template_folder="../../templates",
               url_prefix="/configuration")


@bp.route('/')
def index():
    confs = config.site_data.AppConfiguration().confs
    if confs.epd_brand:
        models = [m.__name__
                  for m in eimage.eta_image.EtaImageGeneratorFactory.models(confs.epd_brand)]
    else:
        models = []

    return render_template("configuration/index.jinja",
                           brands=eimage.eta_image.EtaImageGeneratorFactory.brands(),
                           models=models,
                           app_conf=confs)


@bp.route('/export')
def export():
    confs = config.site_data.AppConfiguration().confs
    return Response(
        json.dumps(confs.model_dump(), indent=4),
        mimetype='application/json',
        headers={'Content-disposition': 'attachment; filename=paper-eta-config.json'})


@bp.route('/import', methods=['POST'])
def import_():
    file = request.files.get('configurations')
    app_conf = config.site_data.AppConfiguration()

    try:
        if file:
            app_conf.update(models.Configuration(**json.load(file)))
    except (pydantic.ValidationError, TypeError):
        flash(lazy_gettext('import_failed'), enums.FlashCategory.error)
    return redirect(url_for('configuration.index'))


@bp.route('/epd')
def epaper_setting():
    confs = config.site_data.AppConfiguration().confs

    if confs.epd_brand:
        models = [m.__name__ for m in eimage.eta_image.EtaImageGeneratorFactory.models(
            confs.epd_brand)]
    else:
        models = []
    return render_template("configuration/epd_form.jinja",
                           brands=eimage.eta_image.EtaImageGeneratorFactory.brands(),
                           models=models,
                           form=forms.EpaperForm(epd_brand=confs.epd_brand,
                                                 epd_model=confs.epd_model))


@bp.route('/api-server')
def api_server_setting():
    conf = config.site_data.AppConfiguration().confs
    return render_template("configuration/api_server_form.jinja",
                           form=forms.ApiServerForm(url=conf.url,
                                                    username=conf.username,
                                                    password=conf.password)
                           )
