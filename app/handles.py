import logging
import traceback

import marshmallow
from flask import Blueprint, current_app, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from flask_babel import lazy_gettext

bp = Blueprint('error_handlers', __name__)


def _need_json_response():
    return request.accept_mimetypes.accept_json and '/api/' in request.path


@bp.app_errorhandler(marshmallow.ValidationError)
def handle_validation_error(err: marshmallow.ValidationError):
    location = list(err.messages_dict.keys())[0]
    return jsonify({
        'success': False,
        'message': "Validation Failed.",
        'data': {
            'errors': err.messages_dict[location],
            'errors_at': location
        }
    }), 400


@bp.app_errorhandler(404)
def error_handler_404(e: HTTPException):
    if _need_json_response():
        return jsonify({
            'success': False,
            'message': 'The requested URL was not found on the server.',
            'data': None
        }), 404
    return render_template('error.jinja', error=e, code=404, msg=e.description)


@bp.app_errorhandler(HTTPException)
def error_handler_all(e: HTTPException):
    if _need_json_response():
        return jsonify({
            'success': False,
            'message': e.description,
            'data': None
        }), e.code
    return render_template('error.jinja', error=e, code=e.code, msg=e.description)


@bp.app_errorhandler(Exception)
def error_handler_all(e: Exception):
    logging.exception(str(e))
    if _need_json_response():
        return jsonify({
            'success': False,
            'message': 'Unexpected internal server error.',
            'data': None if not current_app.debug else {
                'type': e.__class__.__name__,
                'error_message': str(e),
                'traces': traceback.format_exception(e)[1:-1]
            }
        }), 500
    return render_template(
        'error.jinja', error=e, code=500, msg=lazy_gettext('unexpected_error_occured'))
