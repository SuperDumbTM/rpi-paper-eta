import base64
import logging
from io import BytesIO
from pathlib import Path

import webargs
from flask import Blueprint, current_app, jsonify
from flask_babel import lazy_gettext

from app.src import database, site_data, models
from app.src.modules import image as eimage
from app.src.modules import refresher
from app.src.modules.display import epaper

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
        'message': '{}.'.format(lazy_gettext("success")),
        'data': {
            "layouts": eimage.eta_image.EtaImageGeneratorFactory.get_generator(
                args['epd_brand'], args['epd_model']).layouts()
        }
    })


@bp.route("/image")
@webargs.flaskparser.use_args({
    'eta_type': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([t for t in eimage.enums.EtaType])),
    'layout': webargs.fields.String(required=True),
}, location="query")
def image(args):
    app_conf = site_data.AppConfiguration()
    if not app_conf.get('epd_brand') or not app_conf.get('epd_model'):
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext('configuration_required')),
        }), 400

    bookmarks = [models.EtaConfig(**bm.as_dict())
                 for bm in database.db.session.query(database.Bookmark)
                 .order_by(database.Bookmark.ordering)
                 .all()]
    try:
        generator = eimage.eta_image.EtaImageGeneratorFactory().get_generator(
            app_conf.get('epd_brand'), app_conf.get('epd_model')
        )(eimage.enums.EtaType(args['eta_type']), args['layout'])
        images = refresher.generate_image(app_conf, bookmarks, generator)
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
    'eta_type': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([t for t in eimage.enums.EtaType])),
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

    # ---------- generate ETA images ----------
    bookmarks = [models.EtaConfig(**bm.as_dict())
                 for bm in database.db.session.query(database.Bookmark)
                 .order_by(database.Bookmark.ordering)
                 .all()]

    try:
        generator = eimage.eta_image.EtaImageGeneratorFactory().get_generator(
            app_conf.get('epd_brand'), app_conf.get('epd_model')
        )(eimage.enums.EtaType(args['eta_type']), args['layout'])

        images = refresher.generate_image(app_conf, bookmarks, generator)
    except KeyError:
        return jsonify({
            'success': False,
            'message': '{}'.format(lazy_gettext('Layout does not exists.')),
            'data': None
        }), 400

    # ---------- initialise the e-paper controller ----------
    try:
        controller = epaper.ControllerFactory().get_controller(
            app_conf.get('epd_brand'), app_conf.get('epd_model'))(args['is_partial'], False)
    except (OSError, RuntimeError) as e:
        logging.exception("Cannot initialise the e-paper controller.")
        site_data.RefreshHistory().put(models.RefreshLog(**args, error=e))

        return jsonify({
            'success': False,
            'message': '{}'.format(lazy_gettext('Failed to refresh the screen.')),
            'data': None
        }), 400

    # ---------- refresh the e-paper screen ----------
    try:
        if args['is_partial']:
            # load old screen into the display's buffer
            refresher.display_images(
                refresher.cached_images(
                    Path(current_app.config['EPD_IMG_DIR'])),
                controller, False, False)

        refresher.display_images(images, controller, False, False)
        generator.write_images(current_app.config['EPD_IMG_DIR'], images)
        site_data.RefreshHistory().put(models.RefreshLog(**args))
    except Exception as e:
        site_data.RefreshHistory().put(models.RefreshLog(**args, error=e))

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

    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext('success')),
        'data': None
    })
