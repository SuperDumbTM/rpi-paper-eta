import logging

import webargs.flaskparser
from flask import Blueprint, current_app, jsonify, request
from flask_babel import lazy_gettext

from ...src import models, site_data
from ..libs import epd_log, epdcon, eta_img, hketa, refresher

bp = Blueprint('display', __name__, url_prefix="/display")

# ---------------------------------------------
#                       API
# ---------------------------------------------


@bp.route("/refresh")
@webargs.flaskparser.use_args({
    'eta_format': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([t for t in eta_img.enums.EtaFormat])),
    'layout': webargs.fields.String(required=True),
    'is_partial': webargs.fields.Boolean(required=True)
}, location="query")
def refresh(args):
    if (any(p not in request.args for p in ["eta_format", "layout", "is_partial"])):
        return jsonify({
            'success': False,
            'message': "{}{}".format(lazy_gettext('missing_parameter'), lazy_gettext('.')),
            'data': None,
        }), 422
    if (request.args["eta_format"] not in (t for t in eta_img.enums.EtaFormat)):
        return jsonify({
            'success': False,
            'message': "{}{}".format(lazy_gettext('incorrect_parameter'), lazy_gettext('.')),
            'data': None,
        }), 422
    if (not (app_conf := site_data.AppConfiguration()).get('epd_brand')
            or not app_conf.get('epd_model')):
        return jsonify({
            'success': False,
            'message': "{}{}".format(lazy_gettext('configuration_required'), lazy_gettext('.')),
            'data': None,
        }), 422

    # TODO: module name clash
    # ---------- generate ETA images ----------
    bookmarks = [hketa.models.RouteQuery(**bm.as_dict())
                 for bm in models.Bookmark.query.order_by(models.Bookmark.ordering).all()]
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
        }), 422

    # ---------- initialise the e-paper controller ----------
    try:
        controller = epdcon.get(app_conf["epd_brand"],
                                app_conf.get["epd_model"],
                                is_partial=bool(request.args['is_partial']))
    except (OSError, RuntimeError) as e:
        logging.exception("Cannot initialise the e-paper controller.")
        epd_log.epdlog.put(epd_log.Log(**args, error=e))

        return jsonify({
            'success': False,
            'message': '{}'.format(lazy_gettext('Failed to refresh the screen.')),
            'data': None
        }), 503

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
        }), 503
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
    if (not (app_conf := site_data.AppConfiguration()).get('epd_brand')
            or not app_conf.get('epd_model')):
        return jsonify({
            'success': False,
            'message': "{}{}".format(lazy_gettext('configuration_required'), lazy_gettext('.')),
            'data': None,
        }), 422

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
        }), 503
