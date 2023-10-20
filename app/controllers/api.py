from dataclasses import asdict
from typing import Literal

import marshmallow
import requests
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request)

from app import enums, forms, models, mschema
from app.config import site_data

bp = Blueprint('api',
               __name__,
               template_folder="../templates",
               url_prefix="/api")


@bp.route("/setting/server")
def get_server_setting():
    return jsonify({
        'success': True,
        'message': "Success.",
        'data': {
            "setting": mschema.ApiServer().dump(site_data.ApiServerSetting())
        }
    })


@bp.route("/setting/server", methods=["POST", "PUT"])
def update_server_setting():
    schema = mschema.ApiServer()

    try:
        payload = schema.load(request.json)
        site_data.ApiServerSetting().update(**payload).persist()
    except marshmallow.ValidationError as e:
        return jsonify({
            'success': False,
            'message': "Missing/incorrect fields.",
            'data': {
                'errors': [{'field': f, 'error': m[0]} for f, m in e.messages_dict.items()]
            }
        })
    else:
        return jsonify({
            'success': True,
            'message': "Updated.",
            'data': None
        })


@bp.route("/setting/etas")
def get_etas():
    bookmarks = []
    for entry in site_data.EtaList():
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


@bp.route("/setting/eta/<id>", methods=["DELETE"])
def delete_eta(id: str):
    etas = site_data.EtaList()
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


@bp.route('/eta/search/<stype>')
def eta_search(stype: Literal["route", "direction", "service_type", "stop"]):
    if ("company" not in request.args):
        return jsonify({
            'success': False,
            'message': "Missing required query parameter(s)",
            'data': {'missing': [{'company': ["This field is required"]}]}
        }), 422

    try:
        if stype == "route":
            return jsonify({
                'success': True,
                'message': "Success.",
                'data': {
                    'routes': forms.EtaForm.route_choices(request.args['company'])
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
                    'directions': forms.EtaForm.direction_choices(request.args['company'],
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
                    'service_types': forms.EtaForm.type_choices(request.args['company'],
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
                    'stops': forms.EtaForm.stop_choices(request.args['company'],
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


@bp.route("/eta/order", methods=["PUT"])
def eta_swap():
    schema = mschema.EtaOrderChange()

    try:
        payload = schema.load(request.json)

        etas = site_data.EtaList()
        etas.swap(payload['source'], payload['destination']).persist()
    except marshmallow.ValidationError as e:
        return jsonify({
            'success': False,
            'message': "Missing/incorrect fields.",
            'data': {
                'errors': [{'field': f, 'error': m[0]} for f, m in e.messages_dict.items()]
            }
        })
    else:
        return jsonify({
            'success': True,
            'message': "Updated.",
            'data': None
        })
