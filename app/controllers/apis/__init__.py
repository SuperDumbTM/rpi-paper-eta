from webargs.flaskparser import parser
from . import config, display
from app import exceptions

__all__ = [
    config,
    display,
]


@parser.error_handler
def handle_error(error, req, schema, *, error_status_code, error_headers):
    raise error
