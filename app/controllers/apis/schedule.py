from dataclasses import asdict
from typing import Literal

import requests
from flask import Blueprint, current_app,  jsonify, redirect, request
from webargs import fields
from webargs.flaskparser import use_args

from app import enums, forms, models, utils
from app.config import site_data

bp = Blueprint('api_schedule', __name__, url_prefix="/api/schedule")


@bp.route('/schedules')
def get_schedules():
    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            'schedules': []
        }
    })
