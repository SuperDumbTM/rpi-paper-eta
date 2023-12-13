from flask import Blueprint, jsonify

import marshmallow


bp = Blueprint('error_handlers', __name__)


@bp.app_errorhandler(marshmallow.ValidationError)
def handle_validation_error(err: marshmallow.ValidationError):
    location = list(err.messages_dict.keys())[0]
    return jsonify({
        'success': False,
        'message': "",
        'data': {
            'errors': err.messages_dict[location],
            'errors_at': location
        }
    })
