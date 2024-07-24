import json
import logging

import sqlalchemy.exc
from flask import (Blueprint, Response, flash, redirect, render_template,
                   request, url_for)
from flask_babel import lazy_gettext

from paper_eta.src import extensions, forms
from paper_eta.src.libs import hketa

from ....src import db, enums, models, utils

bp = Blueprint('bookmark',
               __name__,
               url_prefix="/")


@bp.route('/bookmarks', methods=["GET", "PUT"])
def index():
    if request.headers.get('HX-Request'):
        if request.method == "PUT":
            bms = models.Bookmark.query.all()
            for bm in bms:
                bm.ordering = request.form.getlist("ids[]").index(str(bm.id))
            db.session.add_all(bms)
            db.session.commit()

        bookmarks = []
        for bm in models.Bookmark.query.order_by(models.Bookmark.ordering).all():
            try:
                stop_name = extensions.hketa.create_route(
                    hketa.models.RouteQuery(**bm.as_dict())).stop_name()
            except Exception:
                stop_name = lazy_gettext('error')
            bookmarks.append(bm.as_dict() | {'stop_name': stop_name})
        return Response(
            render_template("bookmark/partials/rows.jinja",
                            bookmarks=bookmarks),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
    return render_template("bookmark/index.jinja")


@bp.route("/bookmark/<id>", methods=["DELETE"])
def delete(id: str):
    try:
        bookmark = models.Bookmark.query.get(id)
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
        return Response(
            "",
            headers={
                "HX-Reswap": "outterHTML",
                "HX-Retarget": ""
            })


@bp.route('/bookmark/create', methods=["GET", "POST"])
def create():
    form = forms.BookmarkForm()

    if form.validate_on_submit():
        db.session.add(models.Bookmark(**{k: v for k, v in form.data.items()
                                          if k not in ("csrf_token", "submit")}))
        db.session.commit()

        return redirect(url_for("bookmark.index"))

    return render_template("bookmark/edit.jinja",
                           form=form,
                           form_action=url_for("bookmark.create"),
                           editing=False)


@ bp.route('/bookmark/edit/<id>', methods=["GET", "POST"])
def edit(id: str):
    form = forms.BookmarkForm()
    bm: models.Bookmark = models.Bookmark.query.get_or_404(id)

    if form.validate_on_submit():
        for k, v in form.data.items():
            setattr(bm, k, v)
        db.session.merge(bm)
        db.session.commit()
        return redirect(url_for("bookmark.index"))

    form.transport.data = bm.transport.value

    form.no.choices = utils.eta_api.route_choices(bm.transport.value)
    form.no.data = bm.no

    form.direction.choices = utils.eta_api.direction_choices(
        bm.transport.value, bm.no)
    form.direction.data = bm.direction.value

    form.service_type.choices = utils.eta_api.type_choices(
        bm.transport.value, bm.no, bm.direction.value, bm.locale.value
    )
    form.service_type.data = bm.service_type

    form.stop_id.choices = utils.eta_api.stop_choices(
        bm.transport.value, bm.no, bm.direction.value, bm.service_type, bm.locale.value
    )
    form.stop_id.data = bm.stop_id

    return render_template("bookmark/edit.jinja",
                           form=form,
                           transports=[(c.value, lazy_gettext(c.value))
                                       for c in enums.EtaCompany],
                           form_action=url_for("bookmark.edit", id=id),
                           editing=True,)


@bp.route('/bookmark/<transport>/routes')
def routes(transport: str):
    form = forms.BookmarkForm()

    form.no.choices = utils.eta_api.route_choices(transport)
    form.no.data = form.no.choices[0][0]

    return render_template("bookmark/partials/no_input.jinja", form=form)


@bp.route('/bookmark/<transport>/options')
def options(transport: str):
    form = forms.BookmarkForm()
    locale = request.args.get("locale", "en")

    if "pos" not in request.args or request.args.get("no", "") == "":
        pass
    else:
        form.direction.choices = utils.eta_api.direction_choices(
            transport, request.args["no"])
        form.direction.data = request.args.get(
            "direction", form.direction.choices[0][0])

        form.service_type.choices = utils.eta_api.type_choices(
            transport, request.args["no"], form.direction.data, locale
        )
        form.service_type.data = request.args.get(
            "service_type", form.service_type.choices[0][0])

        form.stop_id.choices = utils.eta_api.stop_choices(
            transport, request.args["no"], form.direction.data, form.service_type.data, locale
        )
        form.stop_id.data = request.args.get(
            "stop_id", form.stop_id.choices[0][0])

    return render_template("bookmark/partials/options.jinja", form=form)


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
                except (KeyError, TypeError, sqlalchemy.exc.StatementError):
                    session.rollback()

                    flash(lazy_gettext('Failed to import no. %(entry)s bookmark.', entry=i),
                          enums.FlashCategory.error)
                    logging.exception('Encountering missing field(s) or invalid '
                                      'values during refresh bookmark import.')
    except (UnicodeDecodeError, json.decoder.JSONDecodeError):
        flash(lazy_gettext('import_failed'), enums.FlashCategory.error)
    return redirect(url_for('bookmark.index'))
