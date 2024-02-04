import webargs
from flask import Blueprint, jsonify
from flask_babel import lazy_gettext

from app.src import site_data, database
from app.src.modules import image as eimage

bp = Blueprint('api_config', __name__, url_prefix="/api")


# ------------------------------------------------------------
#                          API Server
# ------------------------------------------------------------


@bp.route("/configs")
def get():
    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("success")),
        'data': {
            'setting': dict(site_data.AppConfiguration())
        }
    })


@bp.route("/config", methods=["POST", "PUT"])
@webargs.flaskparser.use_args({
    'api_url': webargs.fields.Url(),
    # 'api_username': webargs.fields.String(),
    # 'api_password': webargs.fields.String(),
    'epd_brand': webargs.fields.String(
        validate=lambda v: v in eimage.eta_image.EtaImageGeneratorFactory.brands()),
    'epd_model': webargs.fields.String()
})
def update(args):
    app_conf = site_data.AppConfiguration()

    if (app_conf.get('epd_brand') != args['epd_brand']
            or app_conf.get('epd_model') != args['epd_model']):
        # changing brand or model will invalidate the schedule
        database.Schedule.query.update({database.Schedule.enabled: False})
        database.db.session.commit()

    try:
        app_conf.updates(args)
        return jsonify({
            'success': True,
            'message': '{}.'.format(lazy_gettext("updated")),
            'data': None
        })
    except KeyError:
        return jsonify({
            'success': False,
            'message': 'Got unexpected value(s).',
            'data': None
        }), 400
