import json
import logging

import sqlalchemy.exc
from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import gettext, lazy_gettext

from paper_eta.src import database, db, extensions, forms, utils
from paper_eta.src.libs import hketa

bp = Blueprint('bookmark',
               __name__,
               url_prefix="/bookmarks")


@bp.route('/')
def index():
    if request.headers.get('HX-Request'):
        bookmarks = []
        for bm in database.Bookmark.query.order_by(database.Bookmark.ordering).all():
            try:
                stop_name = extensions.hketa.create_route(
                    hketa.RouteQuery(**bm.as_dict())).stop_name()
            except Exception:  # pylint: disable=broad-exception-caught
                stop_name = lazy_gettext('error')
            bookmarks.append(bm.as_dict() | {'stop_name': stop_name})
        return Response(
            render_template("bookmark/partials/rows.jinja",
                            bookmarks=bookmarks),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
    return render_template("bookmark/index.jinja")


@bp.route("/<id_>", methods=["DELETE"])
def delete(id_: str):
    try:
        bookmark = database.Bookmark.query.get(id_)
        db.session.delete(bookmark)
        db.session.commit()
        return Response(
            headers={
                "HX-Location": json.dumps({
                    "path": url_for("bookmark.index"),
                    "target": "tbody",
                    "swap": "innerHTML"
                })}
        )
    except sqlalchemy.exc.SQLAlchemyError:
        return Response("", status=422, headers={"HX-Trigger": json.dumps({
            "toast": {
                "level": "error",
                "message": gettext("invalid_id")
            }
        })})


@bp.route('/create', methods=["GET", "POST"])
def create():
    form = forms.BookmarkForm()

    if form.validate_on_submit():
        db.session.add(database.Bookmark(**{k: v for k, v in form.data.items()
                                            if k not in ("csrf_token", "submit")}))
        db.session.commit()

        return redirect(url_for("bookmark.index"))

    return render_template("bookmark/edit.jinja",
                           form=form,
                           form_action=url_for("bookmark.create"),
                           editing=False)


@ bp.route('/edit/<id_>', methods=["GET", "POST"])
def edit(id_: str):
    form = forms.BookmarkForm()
    bm: database.Bookmark = database.Bookmark.query.get_or_404(id_)

    if form.validate_on_submit():
        for k, v in form.data.items():
            setattr(bm, k, v)
        db.session.merge(bm)
        db.session.commit()
        return redirect(url_for("bookmark.index"))

    form.transport.data = bm.transport.value

    form.no.choices = utils.route_choices(bm.transport.value)
    form.no.data = bm.no

    form.direction.choices = utils.direction_choices(
        bm.transport.value, bm.no)
    form.direction.data = bm.direction.value

    form.service_type.choices = utils.type_choices(
        bm.transport.value, bm.no, bm.direction.value, bm.locale.value
    )
    form.service_type.data = bm.service_type

    form.stop_id.choices = utils.stop_choices(
        bm.transport.value, bm.no, bm.direction.value, bm.service_type, bm.locale.value
    )
    form.stop_id.data = bm.stop_id

    return render_template("bookmark/edit.jinja",
                           form=form,
                           transports=[(c.value, lazy_gettext(c.value))
                                       for c in hketa.Transport],
                           form_action=url_for("bookmark.edit", id_=id_),
                           editing=True,)


@bp.route('/', methods=["PUT"])
def reorder():
    bms = database.Bookmark.query.all()
    for bm in bms:
        bm.ordering = request.form.getlist("ids[]").index(str(bm.id))
    db.session.add_all(bms)
    db.session.commit()

    return Response(
        headers={
            "HX-Location": json.dumps({
                "path": url_for("bookmark.index"),
                "target": "tbody",
                "swap": "innerHTML"
            })}
    )


@bp.route('/<transport>/routes')
def routes(transport: str):
    form = forms.BookmarkForm()

    form.no.choices = utils.route_choices(transport)
    form.no.data = form.no.choices[0][0]

    return render_template("bookmark/partials/no_input.jinja", form=form)


@bp.route('/<transport>/options')
def options(transport: str):
    form = forms.BookmarkForm()
    locale = request.args.get("locale", "en")

    if "pos" not in request.args or request.args.get("no", "") == "":
        pass
    else:
        form.direction.choices = utils.direction_choices(
            transport, request.args["no"])
        form.direction.data = request.args.get(
            "direction", form.direction.choices[0][0])

        form.service_type.choices = utils.type_choices(
            transport, request.args["no"], form.direction.data, locale
        )
        form.service_type.data = request.args.get(
            "service_type", form.service_type.choices[0][0])

        form.stop_id.choices = utils.stop_choices(
            transport, request.args["no"], form.direction.data, form.service_type.data, locale
        )
        form.stop_id.data = request.args.get(
            "stop_id", form.stop_id.choices[0][0])

    return render_template("bookmark/partials/options.jinja", form=form)


@bp.route('/export')
def export():
    return Response(
        json.dumps(
            tuple(map(lambda b: b.as_dict(exclude=['id']),
                      database.Bookmark.query.order_by(database.Bookmark.ordering).all())),
            indent=4),
        mimetype='application/json',
        headers={'Content-disposition': 'attachment; filename=bookmarks.json'})


@bp.route('/import', methods=['POST'])
def import_():
    fields = ({c.name for c in database.Bookmark.__table__.c} -
              {'id', 'created_at', 'updated_at'})  # accepted fields for table inputs
    try:
        for i, bookmark in enumerate(json.load(request.files['bookmarks'].stream)):
            # reference: https://stackoverflow.com/a/76799290
            with db.session.begin_nested() as session:
                try:
                    db.session.add(
                        database.Bookmark(**{k: bookmark.get(k) for k in fields}))
                    db.session.flush()
                except (KeyError, TypeError, sqlalchemy.exc.StatementError):
                    session.rollback()

                    flash(lazy_gettext('Failed to import no. %(entry)s bookmark.', entry=i),
                          "error")
                    logging.exception('Encountering missing field(s) or invalid '
                                      'values during refresh bookmark import.')
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        flash(lazy_gettext('import_failed'), "error")
    return redirect(url_for('bookmark.index'))
