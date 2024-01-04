from datetime import datetime

import croniter
import webargs
from flask import Blueprint, jsonify

from app import config
from app.modules import image as eimage

bp = Blueprint('api_schedule', __name__, url_prefix="/api/schedule")

_schedule_validate_rules = {
    'schedule': webargs.fields.String(
        required=True, validate=lambda v: croniter.croniter.is_valid(v) and len(v.split(' ')) == 5,
        error_messages={'validator_failed': 'Invalid cron expression.'}),
    'eta_type': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([v.value for v in eimage.enums.EtaType])),
    'layout': webargs.fields.String(required=True),
    'is_partial': webargs.fields.Boolean(required=True),
    'enabled': webargs.fields.Boolean(required=True),
}
"""`webargs` validation rules for validating Display Refresh Schedule update endpoints
"""


@bp.route('/schedules')
def get():
    schedules = []
    for s in config.site_data.RefreshSchedule().get_all():
        cron = croniter.croniter(s.schedule, start_time=datetime.now())
        schedules.append({
            **s.model_dump_i18n(),
            'future_executions': (tuple(cron.get_next(datetime).isoformat() for _ in range(10))
                                  if s.enabled else [])
        })

    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            'schedules': schedules
        }
    })


@bp.route('/schedule', methods=['POST'])
@webargs.flaskparser.use_args(_schedule_validate_rules, location="json")
def create(args):
    scheduler = config.site_data.RefreshSchedule()
    scheduler.create(**args)
    return jsonify({
        'success': True,
        'message': "Created.",
        'data': None
    })


@bp.route('/schedule/<id>', methods=['PUT'])
@webargs.flaskparser.use_args(_schedule_validate_rules, location="json")
def update(args, id: str):
    scheduler = config.site_data.RefreshSchedule()
    scheduler.update(**args, id=id)
    return jsonify({
        'success': True,
        'message': "Created.",
        'data': None
    })


@bp.route('/schedule/<id>', methods=["DELETE"])
def delete(id: str):
    try:
        config.site_data.RefreshSchedule().remove(id)
        return jsonify({
            'success': True,
            'message': "Success.",
            'data': None
        })
    except KeyError:
        return jsonify({
            'success': False,
            'message': "Invalid ID.",
            'data': None
        })
