from webargs.flaskparser import parser

from . import display

__all__ = [
    display,
]


@parser.error_handler
def handle_error(error, req, schema, *, error_status_code, error_headers):
    raise error
