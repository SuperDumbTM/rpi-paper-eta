import json

import sqlalchemy.exc
from flask import (Blueprint, Response, redirect, render_template, request,
                   url_for)
from flask_babel import gettext
import sqlalchemy

from paper_eta.src import database, db, exts, forms


bp = Blueprint('bookmark_group', __name__, url_prefix="/bookmark-groups")


@bp.route('/')
def index():
    if request.args.get("action") == "export":
        return Response(
            json.dumps(
                tuple(map(lambda b: b.as_dict(exclude=['id']),
                          database.BookmarkGroup.query.all())),
                indent=4),
            mimetype='application/json',
            headers={'Content-disposition': 'attachment; filename=bookmark_groups.json'})

    if request.headers.get('HX-Request'):
        return Response(
            render_template("bookmark_group/partials/rows.jinja",
                            groups=database.BookmarkGroup.query.all()),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
    return render_template("bookmark_group/index.jinja")


@bp.route('/create', methods=["GET", "POST"])
def create():
    form = forms.BookmarkGroupForm()

    if form.validate_on_submit():
        db.session.add(database.BookmarkGroup(**{k: v for k, v in form.data.items()
                                                 if k not in ("csrf_token", "submit")}
                                              ))
        db.session.commit()
        return redirect(url_for("bookmark_group.index"))

    form.name.data = f"group_{exts.db.session.query(sqlalchemy.func.max(database.BookmarkGroup.id)).scalar() or 0}"
    return render_template("bookmark_group/edit.jinja",
                           form=form,
                           form_action=url_for("bookmark_group.create"),
                           editing=False)


@ bp.route('/edit/<id_>', methods=["GET", "POST"])
def edit(id_: str):
    form = forms.BookmarkGroupForm()
    gp: database.BookmarkGroup = database.BookmarkGroup.query.get_or_404(id_)

    if form.validate_on_submit():
        for k, v in form.data.items():
            setattr(gp, k, v)
        db.session.merge(gp)
        db.session.commit()
        return redirect(url_for("bookmark_group.index"))

    form.name.data = gp.name
    return render_template("bookmark_group/edit.jinja",
                           form=form,
                           form_action=url_for("bookmark_group.edit", id_=id_),
                           editing=True,)


@bp.route("/<id_>", methods=["DELETE"])
def delete(id_: str):
    try:
        db.session.delete(database.BookmarkGroup.query.get_or_404(id_))
        db.session.commit()
        return Response(
            headers={
                "HX-Location": json.dumps({
                    "path": url_for("bookmark_group.index"),
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
