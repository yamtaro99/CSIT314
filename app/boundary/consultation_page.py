from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from app.boundary.session import login_required
from app.control.consultation_controllers import SetAvailabilityController
from app.entity.user_account import UserAccount
from app.entity.interior_designer import InteriorDesigner

bp = Blueprint("consultation", __name__, url_prefix="/consultation")
designer_only = login_required(UserAccount.INTERIOR_DESIGNER)


def display_success(msg):
    flash(msg, "success")


def display_error(msg):
    flash(msg, "error")


@bp.route("/availability", methods=["GET"])
@designer_only
def view_calendar():
    """Steps 1 & 2: ID opens calendar and views current slots[cite: 1]."""
    controller = SetAvailabilityController()
    slots = controller.get_availability_calendar(g.user.user_id)
    return render_template("consultation/calendar.html", slots=slots)


@bp.route("/availability/add", methods=["POST"])
@designer_only
def set_availability():
    date = request.form.get("date")
    start_time = request.form.get("start_time")
    duration = request.form.get("duration", 1)

    # Fetch as an InteriorDesigner instance
    designer = InteriorDesigner.find_by_id(g.user.user_id)

    controller = SetAvailabilityController()
    if controller.set_availability(designer, date, start_time, duration):
        display_success("Consultation availability slot successfully added.")
        return redirect(url_for("consultation.view_calendar"))
    
    for err in controller.errors:
        display_error(err)
    
    return redirect(url_for("consultation.view_calendar"))