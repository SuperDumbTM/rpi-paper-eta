from webargs.flaskparser import parser

from . import bookmark, config, display, log, schedule

__all__ = [
    bookmark,
    config,
    display,
    schedule,
    log,
]


@parser.error_handler
def handle_error(error, req, schema, *, error_status_code, error_headers):
    raise error
