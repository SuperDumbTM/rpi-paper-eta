from webargs.flaskparser import parser
from . import config, display, schedule

__all__ = [
    config,
    display,
    schedule,
]


@parser.error_handler
def handle_error(error, req, schema, *, error_status_code, error_headers):
    print(error)
    raise error
