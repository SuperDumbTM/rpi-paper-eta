from io import BytesIO
import logging
from pathlib import Path

import requests
import webargs
from flask import Blueprint, jsonify, request
from flask_babel import force_locale

from app import config, translation
from app.modules import image as eimage

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


@bp.route("/refresh")
@webargs.flaskparser.use_args({
    'eta_type': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([t for t in eimage.enums.EtaType])),
    'layout': webargs.fields.String(required=True)
}, location="query")
def refresh(args):
    bm_setting = config.site_data.BookmarkList()
    conf = config.site_data.AppConfiguration().confs
    generator = eimage.eta_image.EtaImageGeneratorFactory().get_generator(
        conf.epd_brand, conf.epd_model
    )(eimage.enums.EtaType(args['eta_type']), args['layout'])

    try:
        etas = []
        for bm in bm_setting.get_all():
            res = requests.get(
                f'{conf.url}/{bm.company.value}/{bm.route}/{bm.direction.value}/etas',
                params={
                    'service_type': bm.service_type,
                    'lang': bm.lang,
                    'stop': bm.stop_code}
            ).json()

            logo = (BytesIO(requests.get('{0}{1}'.format(conf.url,
                                                         res['data'].pop(
                                                             'logo_url')
                                                         )).content
                            )
                    if res['data']['logo_url'] is not None
                    else None)

            if res['success']:
                eta = res['data'].pop('etas')
                etas.append(eimage.models.Etas(**res['data'],
                                               etas=[eimage.models.Etas.Eta(**e)
                                                     for e in eta],
                                               logo=logo,
                                               )
                            )
            else:
                with force_locale('en' if bm.lang == 'en' else 'zh_Hant_HK'):
                    res['data'].pop('etas')
                    etas.append(eimage.models.ErrorEta(**res['data'],
                                                       code=res['code'],
                                                       message=str(translation.RP_CODE_TRANSL.get(
                                                           res['code'], res['message'])),
                                                       logo=logo,)
                                )
        images = generator.draw(etas)
    except requests.RequestException as e:
        logging.warning('Image generation failed with error: %s', str(e))
        images = generator.draw_error('Network Error')
    except Exception as e:
        logging.exception('Image generation failed with error: %s', str(e))
        images = generator.draw_error('Unexpected Error')

    generator.write_images(
        Path(config.flask_config.CACHE_DIR).joinpath('epaper'), images)

    return jsonify({
        'success': True
    })
