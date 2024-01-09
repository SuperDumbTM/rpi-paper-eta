from datetime import datetime

import croniter
import webargs
from flask import Blueprint, jsonify
from flask_babel import lazy_gettext

from app import config
from app.modules import image as eimage

bp = Blueprint('api_schedule', __name__, url_prefix="/api")

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
@webargs.flaskparser.use_args({
    'enabled': webargs.fields.Boolean(load_default=None),
    'n_future': webargs.fields.Integer(load_default=5)
}, location="query")
def get_all(args):
    schedules = []
    for s in config.site_data.RefreshSchedule().get_all():
        cron = croniter.croniter(s.schedule, start_time=datetime.now())

        if args['enabled'] is not None and args['enabled'] != s.enabled:
            continue

        schedules.append({
            **s.model_dump(),
            'future_executions': (tuple(cron.get_next(datetime).isoformat() for _ in range(args['n_future']))
                                  if s.enabled else [])
        })

    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("success")),
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
        'message': '{}.'.format(lazy_gettext("created")),
        'data': None
    })


@bp.route('/schedule/<id>', methods=['PUT'])
@webargs.flaskparser.use_args(_schedule_validate_rules, location="json")
def update(args, id: str):
    scheduler = config.site_data.RefreshSchedule()

    try:
        scheduler.update(**args, id=id)
        return jsonify({
            'success': True,
            'message': '{}.'.format(lazy_gettext("updated")),
            'data': None
        })
    except KeyError:
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("invalid_id")),
            'data': None
        }), 400


@bp.route('/schedule/<id>', methods=["DELETE"])
def delete(id: str):
    try:
        config.site_data.RefreshSchedule().remove(id)
        return jsonify({
            'success': True,
            'message': '{}.'.format(lazy_gettext("success")),
            'data': None
        })
    except KeyError:
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("invalid_id")),
            'data': None
        }), 400
