import requests
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request)

from app import enums, forms
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
    form = forms.EtaForm()

    return render_template("configuration/eta.jinja", form=form)


@bp.route('/eta/search')
def eta_search():
    query = request.args

    if ("type" not in request.args or "company" not in request.args):
        pass

    response = requests.get(
        f"{site_data.ApiServerSetting().url}/{request.args['company']}/routes")

    response.json()

    match request.args['type']:
        case "route":
            return jsonify({
                'data': [route['name'] for route in response.json()['data']['routes'].values()]
            })
        case "service_type":
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
