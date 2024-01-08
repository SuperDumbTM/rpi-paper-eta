import webargs
from flask import Blueprint, jsonify

from app import config
from app.modules import image as eimage

bp = Blueprint('api_config', __name__, url_prefix="/api/config")


# ------------------------------------------------------------
#                          API Server
# ------------------------------------------------------------


@bp.route("/eta-server")
def get_server_setting():
    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            'setting': config.site_data.AppConfiguration().confs.model_dump()
        }
    })


@bp.route("/eta-server", methods=["POST", "PUT"])
@webargs.flaskparser.use_args({
    'url': webargs.fields.Url(required=True),
    'username': webargs.fields.String(required=False),
    'password': webargs.fields.String(required=False)
})
def update_server_setting(args):
    aconf = config.site_data.AppConfiguration()
    aconf.update(aconf.confs.model_copy(update=args))
    return jsonify({
        'success': True,
        'message': "Updated.",
        'data': None
    })

# ------------------------------------------------------------
#                          E-Paper
# ------------------------------------------------------------


@bp.route("/epaper", methods=["POST", "PUT"])
@webargs.flaskparser.use_args({
    'epd_brand': webargs.fields.String(
        required=True, validate=lambda v: v in eimage.eta_image.EtaImageGeneratorFactory.brands()),
    'epd_model': webargs.fields.String(required=True)
})
def update_epaper_setting(args):
    aconf = config.site_data.AppConfiguration()
    # TODO: validation

    if aconf.get('epd_brand') != args['epd_brand'] or aconf.get('epd_model') != args['epd_model']:
        # changing brand or model will invalidate the schedule
        scheduler = config.site_data.RefreshSchedule()
        for schedule in scheduler.get_all():
            scheduler.update(**schedule.model_dump(exclude=['enabled']),
                             enabled=False)

    aconf.update(aconf.confs.model_copy(update=args))
    return jsonify({
        'success': True,
        'message': "Updated.",
        'data': None
    })
