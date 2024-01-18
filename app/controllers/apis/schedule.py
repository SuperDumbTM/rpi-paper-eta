from datetime import datetime

import croniter
import webargs
from flask import Blueprint, jsonify
from flask_babel import lazy_gettext

from app import site_data
from app.modules import image as eimage

bp = Blueprint('api_schedule', __name__, url_prefix="/api")


@bp.route('/schedules')
@webargs.flaskparser.use_args({
    'enabled': webargs.fields.Boolean(load_default=None),
    'n_future': webargs.fields.Integer(load_default=5),
    'i18n': webargs.fields.Boolean(load_default=False),
}, location="query")
def get_all(args):
    schedules = []
    for s in site_data.RefreshSchedule().get_all():
        cron = croniter.croniter(s.schedule, start_time=datetime.now())

        if args['enabled'] is not None and args['enabled'] != s.enabled:
            continue

        dump = s.model_dump() if not args['i18n'] else s.model_dump_i18n()
        schedules.append({
            **dump,
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


@bp.route('/schedule/<string:id>')
def get(id: str):
    try:
        return jsonify({
            'success': True,
            'message': '{}.'.format(lazy_gettext("success")),
            'data': {
                'schedule': site_data.RefreshSchedule().get(id).model_dump()
            }
        })
    except KeyError:
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("invalid_id")),
            'data': None
        }), 400


@bp.route('/schedule', methods=['POST'])
@webargs.flaskparser.use_args({
    'schedule': webargs.fields.String(
        required=True, validate=lambda v: croniter.croniter.is_valid(v) and len(v.split(' ')) == 5,
        error_messages={'validator_failed': 'Invalid cron expression.'}),
    'eta_type': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([v.value for v in eimage.enums.EtaType])),
    'layout': webargs.fields.String(required=True),
    'is_partial': webargs.fields.Boolean(required=True),
    'enabled': webargs.fields.Boolean(required=True),
}, location="json")
def create(args):
    scheduler = site_data.RefreshSchedule()
    scheduler.create(**args)
    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("created")),
        'data': None
    })


@bp.route('/schedule/<id>', methods=['PUT'])
@webargs.flaskparser.use_args({
    'schedule': webargs.fields.String(
        validate=lambda v: croniter.croniter.is_valid(
            v) and len(v.split(' ')) == 5,
        error_messages={'validator_failed': 'Invalid cron expression.'}),
    'eta_type': webargs.fields.String(
        validate=webargs.validate.OneOf([v.value for v in eimage.enums.EtaType])),
    'layout': webargs.fields.String(),
    'is_partial': webargs.fields.Boolean(),
    'enabled': webargs.fields.Boolean(),
}, location="json")
def update(args, id: str):
    scheduler = site_data.RefreshSchedule()
    try:
        schedule = scheduler.get(id)
        scheduler.update(**schedule.model_copy(update=args).model_dump())
        return jsonify({
            'success': True,
            'message': '{}.'.format(lazy_gettext("updated")),
            'data': None
        })
    except KeyError as e:
        print(e)
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("invalid_id")),
            'data': None
        }), 400


@bp.route('/schedule/<id>', methods=["DELETE"])
def delete(id: str):
    try:
        site_data.RefreshSchedule().remove(id)
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
