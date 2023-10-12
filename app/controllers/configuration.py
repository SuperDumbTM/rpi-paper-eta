import requests
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request)

from app import enums, forms, models
from app.config import site_data

bp = Blueprint('configuration',
               __name__,
               template_folder="../templates",
               url_prefix="/configuration")


@bp.route('/')
def index():
    return render_template("configuration/index.jinja")


@bp.route('/eta')
def eta():
    return render_template("configuration/eta.jinja", etas=site_data.EtaList())


@bp.route('/eta/new', methods=["GET", "POST"])
def eta_create():
    form = forms.EtaForm()

    if form.validate_on_submit():
        try:
            etas = site_data.EtaList()
            etas.append(models.EtaConfig(**form.data))
            etas.persist()
        except Exception as e:
            current_app.logger.error(e)
            flash("Update failed due to internal errors.",
                  enums.FlashCategory.error)
        else:
            flash("Updated.", enums.FlashCategory.success)

    return render_template("configuration/create_eta.jinja", form=form)


@bp.route('/eta/search')
def eta_search():
    if ("type" not in request.args or "company" not in request.args):
        pass  # TODO: handle missing param

    if request.args['type'] == "route":
        routes: dict[str, dict] = (
            requests.get(
                f"{site_data.ApiServerSetting().url}/{request.args['company']}/routes")
            .json()['data']['routes']
        )

        return jsonify({
            'success': True,
            'message': "Success.",
            'data': {
                'routes': [route['name'] for route in routes.values()]
            }
        })
    elif request.args['type'] == "direction":
        if "route" not in request.args:
            pass  # TODO: handle missing param

        details: dict[str, dict] = (
            requests.get(
                f"{site_data.ApiServerSetting().url}/{request.args['company'].lower()}/{request.args['route'].upper()}")
            .json()['data']
        )

        directions = []
        if details['inbound']:
            directions.append({'name': "回程", 'value': "inbound"})
        if details['outbound']:
            directions.append({'name': "去程", 'value': "outbound"})

        return jsonify({
            'success': True,
            'message': "Success.",
            'data': {
                'direction': directions
            }
        })
    elif request.args['type'] == "service_type":
        if ("route", "direction") not in request.args:
            pass  # TODO: handle missing param

        details: dict[str, dict] = (
            requests.get(
                f"{site_data.ApiServerSetting().url}/{request.args['company'].lower()}/{request.args['route'].upper()}")
            .json()['data']
        )

        return jsonify({
            'success': True,
            'message': "Success.",
            'data': {
                'direction': [{
                    'name': f"{t['service_type']} ({t['orig']['name']['tc']} -> {t['dest']['name']['tc']})",
                    'value': t['service_type']
                } for t in details[request.args['direction'].lower()]]
            }
        })
    elif request.args['type'] == "stop":
        if ("route", "direction", "service_type") not in request.args:
            pass  # TODO: handle missing param

        stops: dict[str, dict] = (
            requests.get(
                f"{site_data.ApiServerSetting().url}/{request.args['company'].lower()}/{request.args['route'].upper()}/{request.args['direction']}/{request.args['service_type']}/stops")
            .json()['data']
        )

        return jsonify({
            'success': True,
            'message': "Success.",
            'data': {
                'stops': [{
                    'name': f"{stop['seq']:02}. {stop['name']['tc']}",
                    'value': stop['seq']
                } for stop in stops['stops']]
            }
        })
    else:
        pass


@bp.route('/epd')
def epd():
    return render_template("configuration/epd.jinja")


@bp.route('/api-server', methods=['GET', 'POST'])
def api_server():
    setting = site_data.ApiServerSetting()
    form = forms.ApiServerForm()

    if form.validate_on_submit():
        try:
            setting.clear().update(url=form.url.data,
                                   username=form.username.data,
                                   password=form.password.data
                                   ).persist()
        except Exception:
            flash("Update failed due to internal errors.",
                  enums.FlashCategory.error)
        else:
            flash("Updated.", enums.FlashCategory.success)
    return render_template("configuration/api_server.jinja",
                           api_url=setting.url,
                           api_username=setting.username,
                           api_password=setting.password,
                           form=form
                           )
