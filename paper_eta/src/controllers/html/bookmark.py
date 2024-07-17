import json
import logging

import requests
from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import lazy_gettext
from sqlalchemy.exc import StatementError

from ....src import db, enums, models, utils

bp = Blueprint('bookmark',
               __name__,
               url_prefix="/")


@bp.route('/bookmarks')
def index():
    return render_template("bookmark/list.jinja")


@bp.route('/bookmark/create')
def create():
    return render_template("bookmark/edit.jinja",
                           transports=[(c.value, lazy_gettext(c.value))
                                       for c in enums.EtaCompany],
                           locales=[(l.value, lazy_gettext(l.value))
                                    for l in enums.EtaLocale],
                           bookmark=models.Bookmark(),
                           form_action=url_for(
                               "api_bookmark.create"),
                           editing=False)


@bp.route('/bookmark/edit/<id>')
def edit(id: str):
    bookmark: models.Bookmark = models.Bookmark.query.get_or_404(id)
    directions = service_types = stops = []
    try:
        directions = utils.eta_api.direction_choices(
            bookmark.transport.value, bookmark.no)
        service_types = utils.eta_api.type_choices(
            bookmark.transport.value, bookmark.no, bookmark.direction.value, bookmark.locale)
        stops = utils.eta_api.stop_choices(
            bookmark.transport.value, bookmark.no, bookmark.direction.value, bookmark.service_type, bookmark.locale)
    except requests.exceptions.ConnectionError:
        flash("API server error.", enums.FlashCategory.error)

    return render_template("bookmark/edit.jinja",
                           transports=[(c.value, lazy_gettext(c.value))
                                       for c in enums.EtaCompany],
                           directions=directions,
                           service_types=service_types,
                           stops=stops,
                           locales=[(l.value, lazy_gettext(l.value))
                                    for l in enums.EtaLocale],
                           bookmark=bookmark,
                           form_action=url_for(
                               "api_bookmark.update", id=id),
                           editing=True,)


@bp.route('/bookmark/export')
def export():
    return Response(
        json.dumps(
            tuple(map(lambda b: b.as_dict(exclude=['id']),
                      models.Bookmark.query.order_by(models.Bookmark.ordering).all())),
            indent=4),
        mimetype='application/json',
        headers={'Content-disposition': 'attachment; filename=bookmarks.json'})


@bp.route('/bookmark/import', methods=['POST'])
def import_():
    fields = ({c.name for c in models.Bookmark.__table__.c} -
              {'id', 'created_at', 'updated_at'})  # accepted fields for table inputs
    try:
        for i, bookmark in enumerate(json.load(request.files['bookmarks'].stream)):
            # reference: https://stackoverflow.com/a/76799290
            with db.session.begin_nested() as session:
                try:
                    db.session.add(
                        models.Bookmark(**{k: bookmark.get(k) for k in fields}))
                    db.session.flush()
                except (KeyError, TypeError, StatementError):
                    session.rollback()

                    flash(lazy_gettext('Failed to import no. %(entry)s bookmark.', entry=i),
                          enums.FlashCategory.error)
                    logging.exception('Encountering missing field(s) or invalid '
                                      'values during refresh bookmark import.')
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        flash(lazy_gettext('import_failed'), enums.FlashCategory.error)
    return redirect(url_for('bookmark.index'))
