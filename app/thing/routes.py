import csv
from datetime import datetime
from io import StringIO

import pytz
from flask import Response, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.exceptions import Forbidden

from app import csrf, db, limiter
from app.models import Thing
from app.thing import bp
from app.thing.forms import ThingFilterForm, ThingForm


@bp.route("/", methods=["GET", "POST"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def list():
    """Get a list of Things."""
    form = ThingFilterForm()

    sort_by = request.args.get("sort", type=str)
    name_query = request.args.get("name", type=str)
    colour = request.args.get("colour", type=str)
    display = request.args.get("display", type=str)

    query = Thing.query

    if name_query:
        query = query.filter(Thing.name.ilike(f"%{name_query}%"))
        form.name.data = name_query
    if colour:
        query = query.filter(Thing.colour == colour)
        form.colour.data = colour
    if display and display == "mine":
        query = query.filter(Thing.user_id == current_user.id)
        form.display.data = display
    if sort_by and sort_by != "name":
        query = query.order_by(getattr(Thing, sort_by).asc(), Thing.name.asc())
        form.sort.data = sort_by
    else:
        query = query.order_by(Thing.name.asc())

    things = query.all()

    total = Thing.query.count()

    return render_template("list_things.html", title="Things", things=things, form=form, total=total)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def create():
    """Create a new Thing."""
    form = ThingForm()

    if form.validate_on_submit():
        new_thing = Thing(
            name=form.name.data.strip(),
            colour=form.colour.data,
            user_id=current_user.id,
        )
        db.session.add(new_thing)
        db.session.commit()
        flash(
            f"<a href='{url_for('thing.view', id=new_thing.id)}' class='alert-link'>{new_thing.name}</a> has been created.",
            "success",
        )
        return redirect(url_for("thing.list"))

    return render_template("create_thing.html", title="Create a new thing", form=form)


@bp.route("/<uuid:id>", methods=["GET"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def view(id):
    """Get a Thing with a specific ID."""
    thing = Thing.query.get_or_404(str(id))

    return render_template("view_thing.html", title=thing.name, thing=thing)


@bp.route("/<uuid:id>/edit", methods=["GET", "POST"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def edit(id):
    """Edit a Thing with a specific ID."""
    thing = Thing.query.get_or_404(str(id))
    if thing not in current_user.things:
        raise Forbidden()
    form = ThingForm()

    if form.validate_on_submit():
        thing.name = form.name.data.strip()
        thing.colour = form.colour.data
        thing.updated_at = pytz.utc.localize(datetime.utcnow())
        db.session.add(thing)
        db.session.commit()
        flash(
            f"Your changes to <a href='{url_for('thing.view', id=thing.id)}' class='alert-link'>{thing.name}</a> have been saved.",
            "success",
        )
        return redirect(url_for("thing.list"))
    elif request.method == "GET":
        form.name.data = thing.name
        form.colour.data = thing.colour

    return render_template(
        "update_thing.html",
        title=f"Edit {thing.name}",
        form=form,
        thing=thing,
    )


@bp.route("/<uuid:id>/delete", methods=["GET", "POST"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
@csrf.exempt
def delete(id):
    """Delete a Thing with a specific ID."""
    thing = Thing.query.get_or_404(str(id))
    if thing not in current_user.things:
        raise Forbidden()

    if request.method == "GET":
        return render_template(
            "delete_thing.html",
            title=f"Delete {thing.name}",
            thing=thing,
        )
    elif request.method == "POST":
        db.session.delete(thing)
        db.session.commit()
        flash(f"{thing.name} has been deleted.", "success")
        return redirect(url_for("thing.list"))


@bp.route("/download", methods=["GET"])
@login_required
@limiter.limit("2 per second", key_func=lambda: current_user.id)
def download():
    """Download a list of Things."""
    sort_by = request.args.get("sort", type=str)
    name_query = request.args.get("name", type=str)
    colour = request.args.get("colour", type=str)

    query = Thing.query

    if name_query:
        query = query.filter(Thing.name.ilike(f"%{name_query}%"))
    if colour:
        query = query.filter(Thing.colour == colour)
    if sort_by and sort_by != "name":
        query = query.order_by(getattr(Thing, sort_by).asc(), Thing.name.asc())
    else:
        query = query.order_by(Thing.name.asc())

    things = query.all()

    def generate():
        data = StringIO()
        w = csv.writer(data)

        # write header
        w.writerow(("ID", "NAME", "COLOUR", "USER_ID", "CREATED_AT", "UPDATED_AT"))
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)

        # write each item
        for thing in things:
            w.writerow(
                (
                    thing.id,
                    thing.name,
                    thing.colour,
                    thing.user_id,
                    thing.created_at.isoformat(),
                    thing.updated_at.isoformat() if thing.updated_at else None,
                )
            )
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)

    response = Response(generate(), mimetype="text/csv", status=200)
    response.headers.set("Content-Disposition", "attachment", filename="things.csv")
    return response
