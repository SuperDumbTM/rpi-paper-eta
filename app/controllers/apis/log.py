import os
import time
from typing import Generator

from flask import Blueprint, Response, current_app, jsonify

bp = Blueprint('api_log', __name__, url_prefix="/api/log")


@bp.route('/')
def get():
    with open(current_app.config['LOG_FILE_PATH'], 'r') as f:
        return jsonify({
            'success': True,
            'message': 'Success.',
            'data': {
                'logs': tuple(next(f).strip('\n') for _ in range(10))
            }
        })


@bp.route('/stream')
def log_stream():
    def _log_stream(path: os.PathLike) -> Generator[str, None, None]:
        """Reference: https://stackoverflow.com/a/3290355
        """
        with open(path, 'r', encoding='utf-8') as f:
            f.seek(0, 2)  # go to the end of the file
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)  # sleep briefly
                    continue
                yield line

    # https://towardsdatascience.com/how-to-add-on-screen-logging-to-your-flask-application-and-deploy-it-on-aws-elastic-beanstalk-aa55907730f
    return Response(_log_stream(current_app.config['LOG_FILE_PATH']),
                    mimetype='text/plain',
                    content_type='text/event-stream')
