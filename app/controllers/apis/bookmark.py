from typing import Literal

import requests
import webargs
from flask import Blueprint, current_app, jsonify, request
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
def get_all():
    bookmarks = []
    for entry in config.site_data.BookmarkList():
        entry: models.EtaConfig

        try:
            stop_name = requests.get(
                f"{config.site_data.AppConfiguration().get('url')}"
                f"/{entry.company.value}/{entry.route}/{entry.direction.value}/{entry.service_type}/stop",
                {'stop_code': entry.stop_code}
            ).json()['data']['stop']['name'][entry.lang]
        except Exception:
            stop_name = lazy_gettext('error')

        bookmarks.append(
            entry.model_dump_i18n() | {'stop_name': stop_name.title()})

    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            "etas": bookmarks
        }
    })


@bp.route("/bookmark", methods=["POST"])
@webargs.flaskparser.use_args(_bookmark_validation_rules)
def create(args):
    bkms = config.site_data.BookmarkList()
    try:
        bkms.create(models.EtaConfig(**args,))
    except KeyError:
        return jsonify({
            'success': False,
            'message': "Invalid ID.",
            'data': None
        }), 400
    else:
        return jsonify({
            'success': True,
            'message': "Updated.",
            'data': None
        })


@bp.route("/bookmark/<id>", methods=["PUT"])
@webargs.flaskparser.use_args(_bookmark_validation_rules)
def update(args, id: str):
    bkms = config.site_data.BookmarkList()
    try:
        bkms.update(id, models.EtaConfig(id=id, **args,))
    except KeyError:
        return jsonify({
            'success': False,
            'message': "Invalid ID.",
            'data': None
        }), 400
    else:
        return jsonify({
            'success': True,
            'message': "Updated.",
            'data': None
        })


@bp.route("/bookmark/<id>", methods=["DELETE"])
def delete(id: str):
    etas = config.site_data.BookmarkList()
    try:
        return jsonify({
            'success': True,
            'message': "Deleted.",
            'data': etas.pop(etas.index(id)).model_dump()
        })
    except ValueError:
        return jsonify({
            'success': False,
            'message': "Invalid ID.",
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
                'message': "Success.",
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
                'message': "Success.",
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
                'message': "Success.",
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
                'message': "Success.",
                'data': {
                    'stops': utils.stop_choices(
                        args['company'], request.args['route'], request.args['direction'],
                        request.args['service_type'], args['lang'])
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': "Endpoint not found.",
                'data': None
            }), 404
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'message': "Connection timeout/error.",
            'data': None
        }), 400
    except requests.exceptions.HTTPError:
        current_app.logger.exception("HTTPError occurs at 'bookmark_search'")
        return jsonify({
            'success': False,
            'message': "Remote server error.",
            'data': None
        }), 400
    except Exception:
        current_app.logger.exception("Unexpected exception.")
        return jsonify({
            'success': False,
            'message': "Unexpected internet error.",
            'data': None
        }), 500


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
        'message': "Updated.",
        'data': None
    })
