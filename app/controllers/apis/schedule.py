from dataclasses import asdict
from typing import Literal

import requests
from cron_validator import CronValidator
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


@bp.route('/schedule', methods=["POST"])
@use_args({
    'schedule': fields.String(required=True),
    'layout': fields.String(required=True),
    'partial_refresh': fields.Boolean(required=True),
}, location="json")
def create_schedule(args):
    try:
        CronValidator.parse(args['schedule'])
    except ValueError:
        return jsonify({
            'success': False,
            'message': "",
            'data': {
                'errors': {
                    'schedule': ['Invalid cron expression']
                },
                'errors_at': 'json'
            }
        })

    scheduler = site_data.RefreshSchedule()
    scheduler.add_job(args['schedule'], args['layout'])
    return jsonify({
        'success': True,
        'message': "Success.",
        'data': None
    })
