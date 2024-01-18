import json
import logging

import pydantic
import requests
from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import lazy_gettext

from app import config, enums, forms, utils

bp = Blueprint('bookmark',
               __name__,
               template_folder="../../templates",
               url_prefix="/")


@bp.route('/bookmarks')
def index():
    return render_template("bookmark/list.jinja", etas=config.site_data.BookmarkList())


@bp.route('/bookmark/create')
def create():
    form = forms.BookmarkForm()

    return render_template("bookmark/edit.jinja",
                           companys=[(c.value, lazy_gettext(c.value))
                                     for c in enums.EtaCompany],
                           langs=[(l.value, lazy_gettext(l.value))
                                  for l in enums.EtaLocale],
                           form=form,
                           form_action=url_for(
                               "api_bookmark.create"),
                           editing=False)


@bp.route('/bookmark/edit/<id>')
def edit(id: str):
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

    return render_template("bookmark/edit.jinja",
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


@bp.route('/bookmark/export')
def export():
    bm = config.site_data.BookmarkList()
    return Response(
        json.dumps(
            tuple(map(lambda s: s.model_dump(exclude=['id']), bm.get_all())),
            indent=4),
        mimetype='application/json',
        headers={'Content-disposition': 'attachment; filename=bookmarks.json'})


@bp.route('/bookmark/import', methods=['POST'])
def import_():
    file = request.files['bookmarks']
    bm = config.site_data.BookmarkList()
    try:
        for i, bookmark in enumerate(json.load(file.stream)):
            try:
                bm.create(**bookmark)
            except (KeyError, pydantic.ValidationError, TypeError):
                flash(lazy_gettext('Failed to import no. %(entry)s bookmark.', entry=i),
                      enums.FlashCategory.error)
                logging.exception(
                    'Encountering missing field(s) or invalid values during refresh bookmark import.')
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        flash(lazy_gettext('import_failed'), enums.FlashCategory.error)
    return redirect(url_for('bookmark.index'))
