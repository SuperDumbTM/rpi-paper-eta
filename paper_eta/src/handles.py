import logging

from flask import Blueprint, render_template
from flask_babel import gettext
from werkzeug.exceptions import HTTPException

bp = Blueprint('error_handlers', __name__)


@bp.app_errorhandler(404)
def error_handler_404(e: HTTPException):
    return render_template('error.jinja',
                           error=e,
                           code=404,
                           msg=gettext("The requested URL was not found on the server."))


@bp.app_errorhandler(HTTPException)
def error_handler_http(e: HTTPException):
    return render_template('error.jinja', error=e, code=e.code, msg=e.description)


@bp.app_errorhandler(Exception)
def error_handler_all(e: Exception):
    logging.exception(str(e))
    return render_template('error.jinja',
                           error=e,
                           code=500,
                           msg=f"{gettext('unexpected_error_occured')}{gettext('.')}")
