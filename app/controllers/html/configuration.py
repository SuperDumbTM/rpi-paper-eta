from flask import Blueprint, render_template

from app import config, forms
from app.modules import image as eimage

bp = Blueprint('configuration',
               __name__,
               template_folder="../../templates",
               url_prefix="/configuration")


@bp.route('/epd')
def epaper_setting():
    conf = config.site_data.AppConfiguration().confs

    if conf.epd_brand:
        models = [m.__name__ for m in eimage.eta_image.EtaImageGeneratorFactory.models(
            conf.epd_brand)]
    else:
        models = []
    return render_template("configuration/epd_form.jinja",
                           brands=eimage.eta_image.EtaImageGeneratorFactory.brands(),
                           models=models,
                           form=forms.EpaperForm(epd_brand=conf.epd_brand,
                                                 epd_model=conf.epd_model))


@bp.route('/api-server')
def api_server_setting():
    conf = config.site_data.AppConfiguration().confs
    return render_template("configuration/api_server_form.jinja",
                           form=forms.ApiServerForm(url=conf.url,
                                                    username=conf.username,
                                                    password=conf.password)
                           )
