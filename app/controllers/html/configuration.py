from dataclasses import asdict
import json
import logging
import pydantic

import requests
from flask import (Blueprint, Response, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_babel import lazy_gettext

from app import enums, forms, models, utils, config
from app.modules import image as eimage

bp = Blueprint('configuration',
               __name__,
               template_folder="../../templates",
               url_prefix="/configuration")


@bp.route('/bookmarks')
def bookmark_list():
    return render_template("configuration/bookmark_list.jinja", etas=config.site_data.BookmarkList())


@bp.route('/bookmark/create')
def bookmark_create():
    form = forms.BookmarkForm()

    return render_template("configuration/bookmark_form.jinja",
                           companys=[(c.value, lazy_gettext(c.value))
                                     for c in enums.EtaCompany],
                           langs=[(l.value, lazy_gettext(l.value))
                                  for l in enums.EtaLocale],
                           form=form,
                           form_action=url_for(
                               "api_bookmark.create"),
                           editing=False)


@bp.route('/bookmark/edit/<id>')
def bookmark_edit(id: str):
    bm = config.site_data.BookmarkList()
    entry = bm.get(id)

    directions = service_types = stops = []
    try:
        directions = utils.direction_choices(entry.company.value, entry.route)
        service_types = utils.type_choices(
            entry.company.value, entry.route, entry.direction.value, entry.lang)
        stops = utils.stop_choices(
            entry.company.value, entry.route, entry.direction.value, entry.service_type, entry.lang)
    except requests.exceptions.ConnectionError:
        flash("API server error.", enums.FlashCategory.error)

    return render_template("configuration/bookmark_form.jinja",
                           companys=[(c.value, lazy_gettext(c.value))
                                     for c in enums.EtaCompany],
                           directions=directions,
                           service_types=service_types,
                           stops=stops,
                           langs=[(l.value, lazy_gettext(l.value))
                                  for l in enums.EtaLocale],
                           form=forms.BookmarkForm(
                               **entry.model_dump(exclude=['id'])),
                           form_action=url_for(
                               "api_bookmark.update", id=id),
                           editing=True,)


@bp.route('/epd')
def epaper_setting():
    conf = config.site_data.AppConfiguration().confs

    if conf.epd_brand:
        models = [m.__name__ for m in eimage.eta_image.EtaImageGeneratorFactory.models(
            conf.epd_brand)]
    else:
        models = []
    return render_template("configuration/epd_form.jinja",
                           brands=eimage.eta_image.EtaImageGeneratorFactory.brands(),
                           models=models,
                           form=forms.EpaperForm(epd_brand=conf.epd_brand,
                                                 epd_model=conf.epd_model))


@bp.route('/api-server')
def api_server_setting():
    conf = config.site_data.AppConfiguration().confs
    return render_template("configuration/api_server_form.jinja",
                           form=forms.ApiServerForm(url=conf.url,
                                                    username=conf.username,
                                                    password=conf.password)
                           )
