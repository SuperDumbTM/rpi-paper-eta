from flask import Blueprint, jsonify, request

from app.modules import image as eimage

bp = Blueprint('api_display',
               __name__,
               template_folder="../../templates",
               url_prefix="/api/display")


@bp.route("/models")
def get_models():
    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            "models": [b.__name__ for b in eimage.eta_image.EtaImageGeneratorFactory.models(request.args['brand'])]
        }
    })


@bp.route("/layouts")
def get_layouts():
    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            "layouts": eimage.eta_image.EtaImageGeneratorFactory.get_generator(
                request.args['brand'], request.args['model']).layouts()
        }
    })
