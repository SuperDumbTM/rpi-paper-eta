from dataclasses import asdict
from typing import Literal

import requests
from flask import Blueprint, current_app,  jsonify, redirect, request
from webargs import fields
from webargs.flaskparser import use_args

from app import enums, forms, models, utils
from app.config import site_data

bp = Blueprint('api_config', __name__, url_prefix="/api/config")


@bp.route("/server")
def get_server_setting():
    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            'setting': site_data.ApiServerSetting().__dict__
        }
    })


@bp.route("/server", methods=["POST", "PUT"])
@use_args({
    'url': fields.URL(required=True),
    'username': fields.Str(required=False),
    'password': fields.Str(required=False)
})
def update_server_setting(args):
    site_data.ApiServerSetting().update(**args).persist()
    return jsonify({
        'success': True,
        'message': "Updated.",
        'data': None
    })


@bp.route("/bookmarks")
def get_etas():
    bookmarks = []
    for entry in site_data.BookmarkList():
        entry: models.EtaConfig

        try:
            stop_name = requests.get(
                f"{site_data.ApiServerSetting().url}"
                f"/{entry.company.value}/{entry.route}/{entry.direction.value}/{entry.service_type}/stop",
                {'stop_code': entry.stop_code}
            ).json()['data']['stop']['name'][entry.lang]
        except Exception:
            stop_name = "Error"
        bookmarks.append(asdict(entry) | {'stop_name': stop_name.title()})

    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            "etas": bookmarks
        }
    })


@bp.route('/bookmark/<stype>')
@use_args({
    'company': fields.String(required=True),
}, location="query")
def eta_search(args, stype: Literal["route", "direction", "service_type", "stop"]):
    print(args)
    try:
        if stype == "route":
            return jsonify({
                'success': True,
                'message': "Success.",
                'data': {
                    'routes': forms.BookmarkForm.route_choices(request.args['company'])
                }
            })
        elif stype == "direction":
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
                    'directions': forms.BookmarkForm.direction_choices(request.args['company'],
                                                                       request.args['route'])
                }
            })
        elif stype == "service_type":
            if ("route", "direction") not in request.args:
                pass  # TODO: handle missing param

            return jsonify({
                'success': True,
                'message': "Success.",
                'data': {
                    'service_types': forms.BookmarkForm.type_choices(request.args['company'],
                                                                     request.args['route'],
                                                                     request.args['direction'])
                }
            })
        elif stype == "stop":
            if ("route", "direction", "service_type") not in request.args:
                pass  # TODO: handle missing param

            return jsonify({
                'success': True,
                'message': "Success.",
                'data': {
                    'stops': forms.BookmarkForm.stop_choices(request.args['company'],
                                                             request.args['route'],
                                                             request.args['direction'],
                                                             request.args['service_type'])
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
        current_app.logger.exception("HTTPError occurs at 'eta_search'")
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


@bp.route("/bookmark/<id>", methods=["DELETE"])
def delete_eta(id: str):
    etas = site_data.BookmarkList()
    try:
        deleted = etas.pop(etas.index(id))
        etas.persist()
        return jsonify({
            'success': True,
            'message': "Deleted.",
            'data': asdict(deleted)
        })
    except ValueError:
        return jsonify({
            'success': False,
            'message': "Invalid ID.",
            'data': None
        }), 400


@bp.route("/bookmark/order", methods=["PUT"])
@use_args({
    'source': fields.Str(required=True),
    'destination': fields.Str(required=True),
})
def eta_swap(args):
    etas = site_data.BookmarkList()
    etas.swap(args['source'], args['destination']).persist()

    return jsonify({
        'success': True,
        'message': "Updated.",
        'data': None
    })


@bp.route("/epaper", methods=["POST", "PUT"])
def update_epaper_setting():
    return jsonify({
        'success': True,
        'message': "Updated.",
        'data': None
    })
