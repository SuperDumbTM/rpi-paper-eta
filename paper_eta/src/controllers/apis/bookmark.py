import sys
from typing import Literal

import requests
import webargs
from flask import Blueprint, abort, current_app, jsonify, request
from flask_babel import lazy_gettext
from webargs import flaskparser

from ... import db, enums, extensions, models, site_data, utils
from ...libs import hketa

bp = Blueprint('api_bookmark', __name__, url_prefix="/api")

_bookmark_validation_rules = {
    'transport': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([c for c in enums.EtaCompany])),
    'no': webargs.fields.String(required=True),
    'direction': webargs.fields.String(required=True),
    'service_type': webargs.fields.String(required=True),
    'stop_id': webargs.fields.String(required=True),
    'locale': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([l for l in enums.EtaLocale]))
}


@bp.route("/bookmarks")
@webargs.flaskparser.use_args({
    'i18n': webargs.fields.Boolean(load_default=False)
}, location="query")
def get_all(args):
    bookmarks = []
    for bm in models.Bookmark.query.order_by(models.Bookmark.ordering).all():
        try:
            stop_name = extensions.hketa.create_route(
                hketa.models.RouteQuery(**bm.as_dict())).stop_name()
        except Exception:
            stop_name = lazy_gettext('error')

        # TODO: i18n for fields
        bookmarks.append(bm.as_dict() | {'stop_name': stop_name})
    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("success")),
        'data': {
            "etas": bookmarks
        }
    })


@bp.route("/bookmark", methods=["POST"])
@webargs.flaskparser.use_args(_bookmark_validation_rules)
def create(args):
    db.session.add(models.Bookmark(**args))
    db.session.commit()
    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("updated")),
        'data': None
    })


@bp.route("/bookmark/<id>", methods=["PUT"])
@webargs.flaskparser.use_args(_bookmark_validation_rules)
def update(args, id: str):
    bookmark = models.Bookmark.query.get_or_404(id)
    for k, v in args.items():
        setattr(bookmark, k, v)

    db.session.merge(bookmark)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("updated")),
        'data': {
            'bookmark': bookmark.as_dict()
        }
    })


@bp.route("/bookmark/<id>", methods=["DELETE"])
def delete(id: str):
    bookmark = models.Bookmark.query.get_or_404(id)
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({
        'success': True,
        'message': "{}.".format(lazy_gettext("deleted")),
        'data': {
            'bookmark': bookmark.as_dict()
        }
    })


@bp.route('/bookmark/<string:search_type>')
def search(search_type: Literal["routes", "directions", "service_types", "stops"]):
    args = flaskparser.parser.parse(
        {
            'transport': webargs.fields.String(
                required=True, validate=webargs.validate.OneOf([c for c in enums.EtaCompany])),
            'locale': webargs.fields.String(
                required=True, validate=webargs.validate.OneOf([c for c in enums.EtaLocale])),
            'no': webargs.fields.String(
                required=search_type in ('directions', 'service_types', 'stops')),
            'direction': webargs.fields.String(
                required=search_type in ('service_types', 'stops')),
            'service_type': webargs.fields.String(
                required=search_type == 'stops'),
        },
        request, location='query'
    )

    try:
        if search_type == "routes":
            return jsonify({
                'success': True,
                'message': '{}.'.format(lazy_gettext("success")),
                'data': {
                    'routes': utils.eta_api.route_choices(args['transport'])
                }
            })
        elif search_type == "directions":
            return jsonify({
                'success': True,
                'message': '{}.'.format(lazy_gettext("success")),
                'data': {
                    'directions': utils.eta_api.direction_choices(args['transport'],
                                                                  args['no'])
                }
            })
        elif search_type == "service_types":
            return jsonify({
                'success': True,
                'message': '{}.'.format(lazy_gettext("success")),
                'data': {
                    'service_types': utils.eta_api.type_choices(args['transport'],
                                                                args['no'],
                                                                args['direction'],
                                                                args['locale'])
                }
            })
        elif search_type == "stops":
            return jsonify({
                'success': True,
                'message': '{}.'.format(lazy_gettext("success")),
                'data': {
                    'stops': utils.eta_api.stop_choices(args['transport'],
                                                        args['no'],
                                                        args['direction'],
                                                        args['service_type'],
                                                        args['locale'])
                }
            })
        else:
            abort(404)
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("connection_error")),
            'data': None
        }), 400
    except requests.exceptions.HTTPError:
        current_app.logger.exception("HTTPError occurs at 'bookmark_search'")
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("eta_server_error")),
            'data': None
        }), 400


@bp.route("/bookmark/order", methods=["PUT"])
@webargs.flaskparser.use_args({
    'src_id': webargs.fields.Integer(required=True),
    'dest_id': webargs.fields.Integer(required=True),
})
def swap(args):
    targets: list[models.Bookmark] = models.Bookmark.query \
        .filter(models.Bookmark.id.in_(args.values())) \
        .all()

    if len(targets) == 2:
        # BUG: possible inconsistent with high traffic
        src_order, dest_order = targets[0].ordering, targets[1].ordering
        targets[0].ordering, targets[1].ordering = sys.maxsize, sys.maxsize - 1
        db.session.add_all(targets)
        db.session.commit()
        targets[0].ordering,  targets[1].ordering = dest_order, src_order
        db.session.add_all(targets)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '{}.'.format(lazy_gettext("updated")),
            'data': None
        })
    else:
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("invalid_id")),
            'data': None
        }), 400
