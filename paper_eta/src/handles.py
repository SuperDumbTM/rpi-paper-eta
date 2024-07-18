import logging
import traceback

import marshmallow
import pydantic
from flask import Blueprint, current_app, jsonify, render_template, request
from flask_babel import lazy_gettext
from werkzeug.exceptions import HTTPException

bp = Blueprint('error_handlers', __name__)


def _need_json_response():
    return request.accept_mimetypes.accept_json and '/api/' in request.path


@bp.app_errorhandler(marshmallow.ValidationError)
def handle_validation_error(e: marshmallow.ValidationError):
    print(e)
    if _need_json_response():
        location = list(e.messages_dict.keys())[0]
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("validation_failed")),
            'data': {
                'errors': e.messages_dict[location],
                'errors_at': location
            }
        }), 422
    return render_template(
        'error.jinja', error=e, code=422, msg="{}.".format(lazy_gettext("validation_failed")))


@bp.app_errorhandler(pydantic.ValidationError)
def handle_pydantic_error(e: pydantic.ValidationError):
    errors: dict[str, list[str]] = {}

    for error in e.errors(include_url=False, include_input=False):
        for location in error['loc']:
            if type(location) is int:
                logging.exception('Encountered int type location.')
                continue
            errors.setdefault(location, [])
            errors[location].append(error['msg'])

    if _need_json_response():
        return jsonify({
            'success': False,
            'message': "{}".format(lazy_gettext("Internal validation failed.")),
            'data': {
                'errors': errors,
                'errors_at': None
            }
        }), 422
    return render_template(
        'error.jinja', error=e, code=422, msg="{}".format(lazy_gettext("Internal validation failed.")))


@bp.app_errorhandler(404)
def error_handler_404(e: HTTPException):
    if _need_json_response():
        return jsonify({
            'success': False,
            'message': "{}".format(lazy_gettext("The requested resource was not found on the server.")),
            'data': None
        }), 404
    return render_template(
        'error.jinja', error=e, code=404, msg="{}".format(lazy_gettext("The requested URL was not found on the server.")))


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
            'message': "{}.".format(lazy_gettext("unexpected_error_occured")),
            'data': None if not current_app.debug else {
                'type': e.__class__.__name__,
                'error_message': str(e),
                'traces': traceback.format_exception(e)[1:-1]
            }
        }), 500
    return render_template(
        'error.jinja', error=e, code=500, msg="{}.".format(lazy_gettext("unexpected_error_occured")))
