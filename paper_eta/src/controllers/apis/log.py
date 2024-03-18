import re

from flask import Blueprint, current_app, jsonify
from flask_babel import lazy_gettext

bp = Blueprint('api_log', __name__, url_prefix="/api/log")


@bp.route('/')
def get():
    # reference: https://stackoverflow.com/a/55284313/17789727
    logs = []
    log_pattern = re.compile(
        r"\[(?P<timestamp>.*?)\]\[(?P<level>[A-Z]*?)\]\[(?P<module>.*?)\]:\s(?P<message>.*)")
    with open(current_app.config['PATH_LOG_FILE'], 'r', encoding='utf-8') as f:
        for line in f:
            match = log_pattern.match(line)
            if not match:
                continue
            logs.append(match.groupdict())

    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext('success')),
        'data': {
            'logs': logs
        }
    })


@bp.route('/', methods=['DELETE'])
def delete():
    open(current_app.config['PATH_LOG_FILE'], 'w', encoding='utf-8').close()
    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext('deleted')),
        'data': None
    })
