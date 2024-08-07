import os
import re
import time
from typing import Generator

from flask import Blueprint, Response, current_app, render_template, request, send_file, url_for

bp = Blueprint('log', __name__, url_prefix="/logs")


@bp.route("/", methods=["GET", "DELETE"])
def index():
    if request.method == "DELETE":
        with open(current_app.config["PATH_LOG_FILE"], "w", encoding="utf-8"):
            pass
        return Response("", headers={"HX-Redirect": url_for("log.index")})
    if request.args.get("action") == "export":
        return send_file(current_app.config['PATH_LOG_FILE'],
                         mimetype='text/plain',
                         as_attachment=True)
    if request.args.get("action") == "raw":
        return send_file(current_app.config['PATH_LOG_FILE'],
                         mimetype='text/plain')

    logs = []
    log_pattern = re.compile(
        r"\[(?P<timestamp>.*?)\]\[(?P<level>[A-Z]*?)\]\[(?P<module>.*?)\]:\s(?P<message>.*)")

    logs = []
    with open(current_app.config['PATH_LOG_FILE'], 'r', encoding='utf-8') as f:
        for line in f:
            match = log_pattern.match(line)
            if not match:
                continue
            logs.append(match.groupdict())
    return render_template("log/index.jinja", logs=logs[::-1])


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
