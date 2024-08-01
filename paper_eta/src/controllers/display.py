import logging

from flask import Blueprint, current_app, jsonify, request
from flask_babel import gettext

from paper_eta.src import database, site_data
from paper_eta.src.libs import epd_log, epdcon, hketa, imgen, refresher

bp = Blueprint('display', __name__, url_prefix="/display")

# ---------------------------------------------
#                       API
# ---------------------------------------------


@bp.route("/refresh")
def refresh():
    if any(p not in request.args for p in ["eta_format", "layout", "is_partial"]):
        return jsonify({
            'success': False,
            'message': gettext("missing_parameter") + gettext("."),
            'data': None,
        }), 422
    if request.args["eta_format"] not in (t for t in imgen.EtaFormat):
        return jsonify({
            'success': False,
            'message': gettext("parameter_not_in_choice") + gettext("."),
            'data': None,
        }), 422
    if not (app_conf := site_data.AppConfiguration()).configurated():
        return jsonify({
            'success': False,
            'message': gettext('missing_app_config'),
            'data': None,
        }), 422

    # TODO: module name clash
    # ---------- generate ETA images ----------
    bookmarks = [hketa.RouteQuery(**bm.as_dict())
                 for bm in database.Bookmark.query.order_by(database.Bookmark.ordering).all()]
    try:
        generator = imgen.get(app_conf.get('epd_brand'), app_conf.get('epd_model')
                              )(imgen.EtaFormat(request.args['eta_format']), request.args['layout'])
        images = refresher.generate_image(bookmarks, generator)
    except KeyError:
        return jsonify({
            'success': False,
            'message': gettext('Layout does not exists.'),
            'data': None
        }), 422

    # ---------- initialise the e-paper controller ----------
    try:
        controller = epdcon.get(app_conf["epd_brand"],
                                app_conf["epd_model"],
                                is_partial=request.args['is_partial'].lower() == "true")
    except (OSError, RuntimeError) as e:
        logging.exception("Cannot initialise the e-paper controller.")
        epd_log.epdlog.put(epd_log.Log(**request.args, error=e))

        return jsonify({
            'success': False,
            'message': gettext('Failed to refresh the screen.'),
            'data': None
        }), 503

    # ---------- refresh the e-paper screen ----------
    try:
        refresher.display_images(refresher.cached_images(current_app.config['DIR_SCREEN_DUMP']),
                                 images,
                                 controller,
                                 False,
                                 True)
    except Exception as e:  # pylint: disable=broad-exception-caught
        epd_log.epdlog.put(epd_log.Log(**request.args, error=e))

        if isinstance(e, RuntimeError):
            logging.exception("Failed to refresh the screen.")
        else:
            logging.exception(
                "An unexpected error occurred during display refreshing.")

        return jsonify({
            'success': False,
            'message': gettext('Failed to refresh the screen.'),
            'data': None
        }), 503

    epd_log.epdlog.put(epd_log.Log(**request.args))
    generator.write_images(current_app.config['DIR_SCREEN_DUMP'], images)

    return jsonify({
        'success': True,
        'message': f"{gettext('success')}{gettext('.')}",
        'data': None
    })


@bp.route("/clear")
def clear_screen():
    if not (app_conf := site_data.AppConfiguration()).configurated():
        return jsonify({
            'success': False,
            'message': gettext('missing_app_config'),
            'data': None,
        }), 422

    try:
        controller = epdcon.get(app_conf['epd_brand'],
                                app_conf['epd_model'],
                                is_partial=False)
        refresher.clear_screen(controller)
        return jsonify({
            'success': True,
            'message': gettext('success') + gettext('.'),
            'data': None,
        })
    except (OSError, RuntimeError):
        logging.exception("Cannot initialise the e-paper controller.")
        return jsonify({
            'success': False,
            'message': gettext('Failed to refresh the screen.'),
            'data': None
        }), 503
