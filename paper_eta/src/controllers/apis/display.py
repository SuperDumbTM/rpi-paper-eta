import base64
import logging
from io import BytesIO

import webargs
from flask import Blueprint, current_app, jsonify
from flask_babel import lazy_gettext

from ....src import models, site_data
from ...libs import epd_log, epdcon, eta_img, hketa, refresher

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
        'message': '{}.'.format(lazy_gettext("success")),
        'data': {
            "models": [b.__name__ for b in eta_img.generator.EtaImageGeneratorFactory.models(args['epd_brand'])]
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
        'message': '{}.'.format(lazy_gettext("success")),
        'data': {
            "layouts": eta_img.generator.EtaImageGeneratorFactory.get_generator(
                args['epd_brand'], args['epd_model']).layouts()
        }
    })


@bp.route("/image")
@webargs.flaskparser.use_args({
    'eta_format': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([t for t in eta_img.enums.EtaFormat])),
    'layout': webargs.fields.String(required=True),
}, location="query")
def image(args):
    app_conf = site_data.AppConfiguration()
    if not app_conf.get('epd_brand') or not app_conf.get('epd_model'):
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext('configuration_required')),
        }), 400

    bookmarks = [hketa.models.RouteQuery(**bm.as_dict())
                 for bm in models.Bookmark.query
                 .order_by(models.Bookmark.ordering)
                 .all()
                 ]
    try:
        generator = eta_img.generator.EtaImageGeneratorFactory().get_generator(
            app_conf.get('epd_brand'), app_conf.get('epd_model')
        )(eta_img.enums.EtaFormat(args['eta_format']), args['layout'])
        images = refresher.generate_image(bookmarks, generator)
    except KeyError:
        return jsonify({
            'success': False,
            'message': '{}'.format(lazy_gettext('Layout does not exists.')),
            'data': None
        }), 400

    for name, img in images.items():
        buffer = BytesIO()
        img.save(buffer, format='bmp')
        images[name] = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext('success')),
        'data': {
            'images': images
        }
    })


@bp.route("/refresh")
@webargs.flaskparser.use_args({
    'eta_format': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([t for t in eta_img.enums.EtaFormat])),
    'layout': webargs.fields.String(required=True),
    'is_partial': webargs.fields.Boolean(required=True)
}, location="query")
def refresh(args):
    app_conf = site_data.AppConfiguration()
    if not app_conf.get('epd_brand') or not app_conf.get('epd_model'):
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext('configuration_required')),
        }), 400

    # TODO: module name clash
    # ---------- generate ETA images ----------
    bookmarks = [hketa.models.RouteQuery(**bm.as_dict())
                 for bm in models.Bookmark.query
                 .order_by(models.Bookmark.ordering)
                 .all()]

    try:
        generator = eta_img.generator.EtaImageGeneratorFactory().get_generator(
            app_conf.get('epd_brand'), app_conf.get('epd_model')
        )(eta_img.enums.EtaFormat(args['eta_format']), args['layout'])

        images = refresher.generate_image(bookmarks, generator)
    except KeyError:
        return jsonify({
            'success': False,
            'message': '{}'.format(lazy_gettext('Layout does not exists.')),
            'data': None
        }), 400

    # ---------- initialise the e-paper controller ----------
    try:
        controller = epdcon.get(app_conf.get('epd_brand'),
                                app_conf.get('epd_model'),
                                is_partial=args['is_partial'])
    except (OSError, RuntimeError) as e:
        logging.exception("Cannot initialise the e-paper controller.")
        epd_log.epdlog.put(epd_log.Log(**args, error=e))

        return jsonify({
            'success': False,
            'message': '{}'.format(lazy_gettext('Failed to refresh the screen.')),
            'data': None
        }), 400

    # ---------- refresh the e-paper screen ----------
    try:
        refresher.display_images(refresher.cached_images(current_app.config['DIR_SCREEN_DUMP']),
                                 images,
                                 controller,
                                 False,
                                 True)
    except Exception as e:
        epd_log.epdlog.put(epd_log.Log(**args, error=e))

        if type(e) is RuntimeError:
            logging.exception("Failed to refresh the screen.")
        else:
            logging.exception(
                "An unexpected error occurred during display refreshing.")

        return jsonify({
            'success': False,
            'message': '{}'.format(lazy_gettext('Failed to refresh the screen.')),
            'data': None
        }), 400
    else:
        epd_log.epdlog.put(epd_log.Log(**args))
        generator.write_images(current_app.config['DIR_SCREEN_DUMP'], images)

    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext('success')),
        'data': None
    })


@bp.route("/clear")
def clear_screen():
    app_conf = site_data.AppConfiguration()
    if not app_conf.get('epd_brand') or not app_conf.get('epd_model'):
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext('configuration_required')),
        }), 400

    try:
        controller = epdcon.get(app_conf.get('epd_brand'),
                                app_conf.get('epd_model'),
                                is_partial=False)
        refresher.clear_screen(controller)
    except (OSError, RuntimeError) as e:
        logging.exception("Cannot initialise the e-paper controller.")
        return jsonify({
            'success': False,
            'message': '{}'.format(lazy_gettext('Failed to refresh the screen.')),
            'data': None
        }), 400
