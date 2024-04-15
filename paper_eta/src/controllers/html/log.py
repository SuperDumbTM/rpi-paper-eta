import os
import time
from typing import Generator

from flask import Blueprint, Response, current_app, render_template, send_file

bp = Blueprint('log', __name__, url_prefix="/log")


@bp.route("/")
def logs():
    return render_template("log/log_table.jinja")


@bp.route('/file')
def download():
    # reference: https://stackoverflow.com/a/55284313/17789727
    return send_file(current_app.config['PATH_LOG_FILE'], mimetype='text/plain', as_attachment=True)


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
                    time.sleep(0.1)
                    continue
                yield line

    # https://towardsdatascience.com/how-to-add-on-screen-logging-to-your-flask-application-and-deploy-it-on-aws-elastic-beanstalk-aa55907730f
    return Response(_log_stream(current_app.config['PATH_LOG_FILE']),
                    mimetype='text/plain',
                    content_type='text/event-stream')
