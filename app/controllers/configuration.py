from dataclasses import asdict
import requests
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)

from app import enums, forms, models, utils
from app.config import site_data

bp = Blueprint('configuration',
               __name__,
               template_folder="../templates",
               url_prefix="/configuration")


@bp.route('/')
def index():
    return render_template("configuration/index.jinja")


@bp.route('/etas')
def eta():
    return render_template("configuration/eta.jinja", etas=site_data.EtaList())


@bp.route('/eta/create', methods=["GET", "POST"])
def eta_create():
    form = forms.EtaForm()

    if form.validate_on_submit():
        try:
            etas = site_data.EtaList()
            etas.create(models.EtaConfig(**form.data)).persist()
        except Exception as e:
            current_app.logger.error(e)
            flash("Update failed due to internal errors.",
                  enums.FlashCategory.error)
        else:
            flash("Updated.", enums.FlashCategory.success)

    return render_template("configuration/eta_form.jinja",
                           form=form,
                           form_action=url_for("configuration.eta_create"),
                           editing=False)


@bp.route('/eta/edit/<id>', methods=["GET", "POST"])
def eta_edit(id: str):
    etas = site_data.EtaList()
    entry = etas.get(id)

    form = forms.EtaForm(data=asdict(entry, dict_factory=utils.asdict_factory))

    form.direction.choices += forms.EtaForm.direction_choices(
        entry.company.value, entry.name)
    form.direction.data = entry.direction.value

    form.service_type.choices += forms.EtaForm.type_choices(
        entry.company.value, entry.name, entry.direction.value)
    form.service_type.data = entry.service_type

    form.stop.choices += forms.EtaForm.stop_choices(
        entry.company.value, entry.name, entry.direction.value, entry.service_type)
    form.stop.data = entry.stop

    if form.validate_on_submit():
        try:
            etas.update(id, models.EtaConfig(**form.data, id=id)).persist()
        except ValueError:
            flash("Invalid ETA entry ID.", enums.FlashCategory.error)
        except Exception as e:
            current_app.logger.error(e)
            flash("Update failed due to internal errors.",
                  enums.FlashCategory.error)
        else:
            flash("Updated.", enums.FlashCategory.success)

    return render_template("configuration/eta_form.jinja",
                           form=form,
                           form_action=url_for(
                               "configuration.eta_edit", id=id),
                           editing=True)


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
