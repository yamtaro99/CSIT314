from flask import Blueprint, flash, redirect, render_template, url_for

from app.boundary.session import login_required
from app.control.id_application_controller import IDApplicationController
from app.entity.user_account import UserAccount

bp = Blueprint("application_review", __name__, url_prefix="/admin/id-applications")
admin_only = login_required(UserAccount.USER_ADMIN)


def display_success(msg):
    flash(msg, "success")


def display_error(msg):
    flash(msg, "error")


def display_application(applications):
    return render_template("application_review/review.html", applications=applications)


@bp.route("/")
@admin_only
def view_id_applications():
    applications = IDApplicationController().get_pending_application()
    return display_application(applications)


@bp.route("/<int:user_id>/approve", methods=["POST"])
@admin_only
def approve_application(user_id):
    controller = IDApplicationController()
    if controller.approve_application(user_id):
        display_success("Application approved")
    else:
        for err in controller.errors:
            display_error(err)
    return redirect(url_for("application_review.view_id_applications"))