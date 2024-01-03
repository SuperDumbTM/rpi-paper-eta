from io import BytesIO
import logging
from pathlib import Path

import requests
import webargs
from flask import Blueprint, jsonify, request
from flask_babel import force_locale

from app import config, models, translation
from app.modules import image as eimage
from app.modules import refresher
from app.modules.display import epaper

bp = Blueprint('api_display',
               __name__,
               template_folder="../../templates",
               url_prefix="/api/display")


@bp.route("/models")
@webargs.flaskparser.use_args({
    'epd_brand': webargs.fields.String(required=True)
}, location='query')
def get_models(args):
    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            "models": [b.__name__ for b in eimage.eta_image.EtaImageGeneratorFactory.models(args['epd_brand'])]
        }
    })


@bp.route("/layouts")
@webargs.flaskparser.use_args({
    'epd_brand': webargs.fields.String(required=True),
    'epd_model': webargs.fields.String(required=True)
}, location='query')
def get_layouts(args):
    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            "layouts": eimage.eta_image.EtaImageGeneratorFactory.get_generator(
                args['epd_brand'], args['epd_model']).layouts()
        }
    })


@bp.route("/refresh", methods=['POST'])
@webargs.flaskparser.use_args({
    'eta_type': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([t for t in eimage.enums.EtaType])),
    'layout': webargs.fields.String(required=True),
    'is_partial': webargs.fields.Boolean(required=True)
})
def refresh(args):
    aconf = config.site_data.AppConfiguration()
    if (not aconf.confs.epd_brand or not aconf.confs.epd_model):
        return jsonify({
            'success': False
        })

    bm_setting = config.site_data.BookmarkList()
    generator = eimage.eta_image.EtaImageGeneratorFactory().get_generator(
        aconf.confs.epd_brand, aconf.confs.epd_model
    )(eimage.enums.EtaType(args['eta_type']), args['layout'])
    images = refresher.generate_image(aconf.confs,
                                      bm_setting.get_all(),
                                      generator)

    try:
        controller = epaper.ControllerFactory().get_controller(
            aconf.confs.epd_brand, aconf.confs.epd_model)(args['is_partial'])

        with controller:
            controller.display(images)

            if (args['is_partial']):
                # load the old image into the display's buffer
                controller.display(refresher.cached_images(
                    Path(config.flask_config.CACHE_DIR).joinpath('epaper')))

            controller.display(images)

        generator.write_images(
            Path(config.flask_config.CACHE_DIR).joinpath('epaper'), images)
        config.site_data.RefreshHistory().put(models.RefreshLog(**args))
    except OSError as e:
        logging.exception(
            "Unable to connect the E-paper due to unsupported platform.")
        config.site_data.RefreshHistory().put(models.RefreshLog(**args, error=e))
    except Exception as e:
        logging.exception(
            "An unexpected error occurred.")
        config.site_data.RefreshHistory().put(models.RefreshLog(**args, error=e))

    return jsonify({
        'success': True
    })
