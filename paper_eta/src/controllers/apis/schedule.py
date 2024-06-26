from datetime import datetime

import croniter
import webargs
from flask import Blueprint, jsonify
from flask_babel import lazy_gettext

from ....src import db, models
from ...libs import eta_img

bp = Blueprint('api_schedule', __name__, url_prefix="/api")


@bp.route('/schedules')
@webargs.flaskparser.use_args({
    'enabled': webargs.fields.Boolean(load_default=None),
    'n_future': webargs.fields.Integer(load_default=5),
    'i18n': webargs.fields.Boolean(load_default=False),
}, location="query")
def get_all(args):
    schedules = []
    for schedule in models.Schedule.query.all():
        schedule: models.Schedule

        cron = croniter.croniter(schedule.schedule, start_time=datetime.now())
        if args['enabled'] is not None and args['enabled'] != schedule.enabled:
            continue

        # TODO: i18n for eta_mode
        schedules.append({
            **dict(schedule.as_dict()),
            'future_executions': (tuple(cron.get_next(datetime).isoformat() for _ in range(args['n_future']))
                                  if schedule.enabled else [])
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
    schedule = models.Schedule.query.get(id)
    if schedule:
        return jsonify({
            'success': True,
            'message': '{}.'.format(lazy_gettext("success")),
            'data': {
                'schedule': schedule.as_dict()
            }
        })
    else:
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
    'eta_format': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([v.value for v in eta_img.enums.EtaFormat])),
    'layout': webargs.fields.String(required=True),
    'is_partial': webargs.fields.Boolean(required=True),
    'enabled': webargs.fields.Boolean(required=True),
}, location="json")
def create(args):
    db.session.add(models.Schedule(**args))
    db.session.commit()
    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("created")),
        'data': None
    })


@bp.route('/schedule/<string:id>', methods=['PUT'])
@webargs.flaskparser.use_args({
    'schedule': webargs.fields.String(
        validate=lambda v: croniter.croniter.is_valid(
            v) and len(v.split(' ')) == 5,
        error_messages={'validator_failed': 'Invalid cron expression.'}),
    'eta_format': webargs.fields.String(
        validate=webargs.validate.OneOf([v.value for v in eta_img.enums.EtaFormat])),
    'layout': webargs.fields.String(),
    'is_partial': webargs.fields.Boolean(),
    'enabled': webargs.fields.Boolean(),
}, location="json")
def update(args, id: str):
    schedule = models.Schedule.query.get_or_404(id)
    for k, v in args.items():
        setattr(schedule, k, v)

    db.session.merge(schedule)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("updated")),
        'data': {
            'schedule': schedule.as_dict()
        }
    })


@bp.route('/schedule/<string:id>', methods=["DELETE"])
def delete(id: str):
    schedule = models.Schedule.query.get_or_404(id)
    db.session.delete(schedule)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("success")),
        'data': {
            'schedule': schedule.as_dict()
        }
    })
