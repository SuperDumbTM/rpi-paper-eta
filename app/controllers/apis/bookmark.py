from typing import Literal

import requests
import webargs
from flask import Blueprint, abort, current_app, jsonify, request
from flask_babel import lazy_gettext

from app import config, enums, models, utils

bp = Blueprint('api_bookmark', __name__, url_prefix="/api")

_bookmark_validation_rules = {
    'company': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([c for c in enums.EtaCompany])),
    'route': webargs.fields.String(required=True),
    'direction': webargs.fields.String(required=True),
    'service_type': webargs.fields.String(required=True),
    'stop_code': webargs.fields.String(required=True),
    'lang': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([l for l in enums.EtaLocale]))
}


@bp.route("/bookmarks")
@webargs.flaskparser.use_args({
    'i18n': webargs.fields.Boolean(load_default=False)
}, location="query")
def get_all(args):
    bookmarks = []
    for bm in config.site_data.BookmarkList():
        bm: models.EtaConfig

        try:
            stop_name = requests.get(
                f"{config.site_data.AppConfiguration().get('url')}"
                f"/{bm.company.value}/{bm.route}/{bm.direction.value}/{bm.service_type}/stop",
                {'stop_code': bm.stop_code}
            ).json()['data']['stop']['name'][bm.lang]
        except Exception:
            stop_name = lazy_gettext('error')

        dump = (bm.model_dump()if not args['i18n'] else bm.model_dump_i18n())
        bookmarks.append(dump | {'stop_name': stop_name})

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
    bkms = config.site_data.BookmarkList()
    try:
        bkms.create(**args)
    except KeyError:
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("invalid_id")),
            'data': None
        }), 400
    else:
        return jsonify({
            'success': True,
            'message': '{}.'.format(lazy_gettext("updated")),
            'data': None
        })


@bp.route("/bookmark/<id>", methods=["PUT"])
@webargs.flaskparser.use_args(_bookmark_validation_rules)
def update(args, id: str):
    bkms = config.site_data.BookmarkList()
    try:
        print(args)
        bkms.update(id, **args)
    except KeyError:
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("invalid_id")),
            'data': None
        }), 400
    else:
        return jsonify({
            'success': True,
            'message': '{}.'.format(lazy_gettext("updated")),
            'data': None
        })


@bp.route("/bookmark/<id>", methods=["DELETE"])
def delete(id: str):
    etas = config.site_data.BookmarkList()
    try:
        return jsonify({
            'success': True,
            'message': "{}.".format(lazy_gettext("deleted")),
            'data': etas.pop(etas.index(id)).model_dump()
        })
    except ValueError:
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("invalid_id")),
            'data': None
        }), 400


@bp.route('/bookmark/<string:search_type>')
@webargs.flaskparser.use_args({
    'company': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([c for c in enums.EtaCompany])),
    'lang': webargs.fields.String(
        required=True, validate=webargs.validate.OneOf([c for c in enums.EtaLocale]))
}, location="query")
def search(args,
           search_type: Literal["routes", "directions", "service_types", "stops"]):
    try:
        if search_type == "routes":
            return jsonify({
                'success': True,
                'message': '{}.'.format(lazy_gettext("success")),
                'data': {
                    'routes': utils.route_choices(args['company'])
                }
            })
        elif search_type == "directions":
            if "route" not in request.args:
                return jsonify({
                    'success': False,
                    'message': "Missing required query parameter(s)",
                    'data': {'missing': [{'route': ["This field is required"]}]}
                }), 422

            return jsonify({
                'success': True,
                'message': '{}.'.format(lazy_gettext("success")),
                'data': {
                    'directions': utils.direction_choices(
                        args['company'], request.args['route'])
                }
            })
        elif search_type == "service_types":
            if ("route", "direction") not in request.args:
                pass  # TODO: handle missing param

            return jsonify({
                'success': True,
                'message': '{}.'.format(lazy_gettext("success")),
                'data': {
                    'service_types': utils.type_choices(
                        args['company'], request.args['route'],
                        request.args['direction'], args['lang'])
                }
            })
        elif search_type == "stops":
            if ("route", "direction", "service_type") not in request.args:
                pass  # TODO: handle missing param

            return jsonify({
                'success': True,
                'message': '{}.'.format(lazy_gettext("success")),
                'data': {
                    'stops': utils.stop_choices(
                        args['company'], request.args['route'], request.args['direction'],
                        request.args['service_type'], args['lang'])
                }
            })
        else:
            abort(404)
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("connection_error")),
            'data': None
        })
    except requests.exceptions.HTTPError:
        current_app.logger.exception("HTTPError occurs at 'bookmark_search'")
        return jsonify({
            'success': False,
            'message': '{}.'.format(lazy_gettext("eta_server_error")),
            'data': None
        })


@bp.route("/bookmark/order", methods=["PUT"])
@webargs.flaskparser.use_args({
    'source': webargs.fields.String(required=True),
    'destination': webargs.fields.String(required=True),
})
def swap(args):
    etas = config.site_data.BookmarkList()
    etas.swap(args['source'], args['destination'])

    return jsonify({
        'success': True,
        'message': '{}.'.format(lazy_gettext("updated")),
        'data': None
    })
