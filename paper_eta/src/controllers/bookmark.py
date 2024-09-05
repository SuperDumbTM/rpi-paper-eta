import json
import logging

import sqlalchemy.exc
from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import gettext, lazy_gettext

from paper_eta.src import database, db, exts, forms, site_data, utils
from paper_eta.src.libs import hketa


# --------------------------------------------------
# Endpoints that require "bgid" in query param:
#   1. GET /
#   2. POST /
#   3. PUT /
#   4. GET /create
# --------------------------------------------------

bp = Blueprint('bookmark', __name__, url_prefix="/bookmarks")


def _get_bm_q():
    if request.args.get("bgid"):
        return exts.db.session\
            .query(database.Bookmark)\
            .filter(database.Bookmark.bookmark_group_id == request.args["bgid"])
    return exts.db.session\
        .query(database.Bookmark)\
        .filter(database.Bookmark.bookmark_group_id.is_(None))


@bp.route('/')
def index():
    if request.args.get("action") == "export":
        return Response(
            json.dumps(
                tuple(map(lambda b: b.as_dict(exclude=['id']),
                          _get_bm_q().order_by(database.Bookmark.ordering).all())),
                indent=4),
            mimetype='application/json',
            headers={'Content-disposition': 'attachment; filename=bookmarks.json'})

    if request.headers.get('HX-Request'):
        bookmarks = []
        for bm in _get_bm_q().order_by(database.Bookmark.ordering).all():
            try:
                bm.stop_name = exts.hketa.create_route(
                    hketa.RouteQuery(**bm.as_dict())).stop_name()
            except Exception:  # pylint: disable=broad-exception-caught
                bm.stop_name = lazy_gettext('error')
            bookmarks.append(bm)
        return Response(
            render_template("bookmark/partials/rows.jinja",
                            bookmarks=bookmarks),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )

    if request.args.get("bgid"):
        return render_template("bookmark/index.jinja", group=database.BookmarkGroup.query.get_or_404(request.args["bgid"]))
    return render_template("bookmark/index.jinja", group=None)


@bp.route('/', methods=['POST'])
def import_():
    fields = ({c.name for c in database.Bookmark.__table__.c} -
              {'id', 'created_at', 'updated_at'})  # accepted fields for table inputs
    try:
        for i, bookmark in enumerate(json.load(request.files['bookmarks'].stream)):
            # reference: https://stackoverflow.com/a/76799290
            with db.session.begin_nested() as session:
                try:
                    db.session.add(
                        database.Bookmark(**{k: bookmark.get(k) for k in fields} | {
                            "locale": site_data.AppConfiguration().get("eta_locale", "en")
                        }))
                    db.session.flush()
                except (KeyError, TypeError, sqlalchemy.exc.StatementError) as e:
                    session.rollback()

                    flash(lazy_gettext('Failed to import no. %(entry)s bookmark.', entry=i),
                          "error")
                    logging.exception('During bookmark import: %s', str(e))
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        flash(lazy_gettext('import_failed'), "error")
    return redirect(url_for('bookmark.index', bgid=request.args.get("bgid")))


@bp.route('/create', methods=["GET", "POST"])
def create():
    form = forms.BookmarkForm()

    if form.validate_on_submit():
        app_conf = site_data.AppConfiguration()
        db.session.add(database.Bookmark(**{k: v for k, v in form.data.items()
                                            if k not in ("csrf_token", "submit")} | {
                                                "locale": app_conf["eta_locale"]}
                                         ))
        db.session.commit()
        return redirect(url_for("bookmark.index", bgid=form.bookmark_group_id.data))

    form.bookmark_group_id.data = request.args.get("bgid")
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
        return redirect(url_for("bookmark.index", bgid=form.bookmark_group_id.data))

    form.bookmark_group_id.data = bm.bookmark_group_id

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
                                       for c in hketa.Company],
                           form_action=url_for("bookmark.edit", id_=id_),
                           editing=True,)


@bp.route('/status/<id_>', methods=["PUT"])
def toggle_status(id_: str):
    try:
        bookmark = database.Bookmark.query.get_or_404(id_)
        setattr(bookmark, "enabled", not bookmark.enabled)
        db.session.commit()
        return Response(
            headers={
                "HX-Location": json.dumps({
                    "path": url_for("bookmark.index", bgid=bookmark.bookmark_group_id),
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


@bp.route('/', methods=["PUT"])
def reorder():
    bms = _get_bm_q().all()
    for bm in bms:
        bm.ordering = request.form.getlist("ids[]").index(str(bm.id))
    db.session.add_all(bms)
    db.session.commit()

    return Response(
        headers={
            "HX-Location": json.dumps({
                "path": url_for("bookmark.index", bgid=request.args.get("bgid")),
                "target": "tbody",
                "swap": "innerHTML"
            })}
    )


@bp.route("/<id_>", methods=["DELETE"])
def delete(id_: str):
    try:
        bookmark = database.Bookmark.query.get_or_404(id_)
        db.session.delete(bookmark)
        db.session.commit()
        return Response(
            headers={
                "HX-Location": json.dumps({
                    "path": url_for("bookmark.index", bgid=bookmark.bookmark_group_id),
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


# --------------------------------------------------
#               Form HTMX Handlers
# --------------------------------------------------


@bp.route('/<transport>/routes')
def routes(transport: str):
    form = forms.BookmarkForm()

    form.no.choices = utils.route_choices(transport)
    form.no.data = form.no.choices[0][0]

    return render_template("bookmark/partials/no_input.jinja", form=form)


@bp.route('/<transport>/options')
def options(transport: str):
    form = forms.BookmarkForm()
    locale = site_data.AppConfiguration().get("eta_locale",
                                              (hketa.Locale.TC.value
                                               if utils.get_locale() == "zh_Hant_HK"
                                               else hketa.Locale.EN.value))

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
