from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.boundary.session import login_required
from app.control.id_application_controller import IDApplicationController
from app.entity.user_account import UserAccount

bp = Blueprint("application_review", __name__, url_prefix="/admin/id-applications")
admin_only = login_required(UserAccount.USER_ADMIN)


class ApplicationReviewPage:
    def display_success(self, msg):
        flash(msg, "success")

    def display_error(self, msg):
        flash(msg, "error")

    def display_application(self, applications):
        return render_template("application_review/review.html", applications=applications)

    def display_application_details(self, designer):
        return render_template("application_review/detail.html", designer=designer)

    def _to_list(self):
        return redirect(url_for("application_review.view_id_applications"))

    def _to_details(self, user_id):
        return redirect(url_for("application_review.view_application_details", user_id=user_id))

    def view_id_applications(self):
        applications = IDApplicationController().get_pending_application()
        return self.display_application(applications)

    def view_application_details(self, user_id):
        designer = IDApplicationController().get_application(user_id)
        if designer is None:
            self.display_error("Application not found or no longer pending")
            return self._to_list()
        return self.display_application_details(designer)

    def approve_application(self, user_id):
        controller = IDApplicationController()
        if controller.approve_application(user_id):
            self.display_success(f"Application approved for {controller.designer.name}")
            return self._to_list()
        for err in controller.errors:
            self.display_error(err)
        return self._to_list()

    def reject_application(self, user_id):
        controller = IDApplicationController()
        if controller.reject_application(user_id):
            self.display_success(f"Application rejected for {controller.designer.name}")
            return self._to_list()
        for err in controller.errors:
            self.display_error(err)
        return self._to_list()

    def request_additional_docs(self, user_id):
        controller = IDApplicationController()
        if controller.request_additional_docs(user_id, request.form.get("remarks", "")):
            self.display_success(f"Additional documents requested from {controller.designer.name}")
            return self._to_details(user_id)
        for err in controller.errors:
            self.display_error(err)
        return self._to_details(user_id)


page = ApplicationReviewPage()


@bp.route("/")
@admin_only
def view_id_applications():
    return page.view_id_applications()


@bp.route("/<int:user_id>")
@admin_only
def view_application_details(user_id):
    return page.view_application_details(user_id)


@bp.route("/<int:user_id>/approve", methods=["POST"])
@admin_only
def approve_application(user_id):
    return page.approve_application(user_id)


@bp.route("/<int:user_id>/reject", methods=["POST"])
@admin_only
def reject_application(user_id):
    return page.reject_application(user_id)


@bp.route("/<int:user_id>/request-docs", methods=["POST"])
@admin_only
def request_additional_docs(user_id):
    return page.request_additional_docs(user_id)