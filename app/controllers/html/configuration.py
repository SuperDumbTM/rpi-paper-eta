from dataclasses import asdict
import requests
from flask import (Blueprint, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)

from app import enums, forms, models, utils
from app.config import site_data
from app.modules import image as eimage

bp = Blueprint('configuration',
               __name__,
               template_folder="../../templates",
               url_prefix="/configuration")


@bp.route('/bookmarks')
def bookmark_list():
    return render_template("configuration/bookmark_list.jinja", etas=site_data.BookmarkList())


# @bp.route('/bookmark/create', methods=["GET", "POST"])
# def bookmark_create():
#     form = forms.BookmarkForm()

#     if form.validate_on_submit():
#         try:
#             etas = site_data.BookmarkList()
#             etas.create(models.EtaConfig(**form.data)).persist()
#         except Exception as e:
#             current_app.logger.error(e)
#             flash("Update failed due to internal errors.",
#                   enums.FlashCategory.error)
#         else:
#             flash("Updated.", enums.FlashCategory.success)

#     return render_template("configuration/bookmark_form.jinja",
#                            form=form,
#                            form_action=url_for(
#                                "configuration.bookmark_create"),
#                            editing=False)

@bp.route('/bookmark/create')
def bookmark_create():
    form = forms.BookmarkForm()

    return render_template("configuration/bookmark_form.jinja",
                           companys=[(c.value, c.name)
                                     for c in enums.EtaCompany],
                           langs=[(l.value, l.name)
                                  for l in enums.Locale],
                           form=form,
                           form_action=url_for(
                               "api_config.bookmark_create"),
                           editing=False)


@bp.route('/bookmarks/edit/<id>')
def bookmark_edit(id: str):
    etas = site_data.BookmarkList()
    entry = etas.get(id)

    directions = service_types = stops = []
    try:
        directions = utils.direction_choices(entry.company.value, entry.route)
        service_types = utils.type_choices(
            entry.company.value, entry.route, entry.direction.value)
        stops = utils.stop_choices(
            entry.company.value, entry.route, entry.direction.value, entry.service_type)
    except requests.exceptions.ConnectionError:
        flash("API server error.", enums.FlashCategory.error)

    return render_template("configuration/bookmark_form.jinja",
                           companys=[(c.value, c.name)
                                     for c in enums.EtaCompany],
                           directions=directions,
                           service_types=service_types,
                           stops=stops,
                           langs=[(l.value, l.name)
                                  for l in enums.Locale],
                           form=forms.BookmarkForm(
                               **entry.model_dump(exclude=['id'])),
                           form_action=url_for(
                               "api_config.bookmark_update", id=id),
                           editing=True,)


@bp.route('/epd')
def epaper_setting():
    setting = site_data.EpaperSetting()
    return render_template("configuration/epd_form.jinja",
                           brands=eimage.eta_image.EtaImageGeneratorFactory.brands(),
                           form=forms.EpaperForm(brand=setting.brand,
                                                 model=setting.model))


@bp.route('/api-server')
def api_server_setting():
    setting = site_data.ApiServerSetting()

    return render_template("configuration/api_server_form.jinja",
                           form=forms.ApiServerForm(url=setting.url,
                                                    username=setting.username,
                                                    password=setting.password)
                           )
