from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.boundary.session import login_required

from app.control.admin_controllers import ViewApplicationController, ApproveApplicationController, RejectApplicationController

from app.entity.user_account import UserAccount

bp = Blueprint("admin", __name__, url_prefix="/admin")
admin_only = login_required(UserAccount.USER_ADMIN)


class ApplicationReviewPage:
    
    def view_id_applications(self):
        applications = ViewApplicationController().get_pending_application()
        return self.display_application(applications)
    
    def display_application(self, applications):
        return render_template("admin/pending_applications.html", applications=applications)

    def view_application_details(self, user_id):
        controller = ViewApplicationController()
        designer = controller.get_application(user_id)
        if designer is None:
            self.display_error("Application not found or no longer pending")
            return self._to_list()
        company = controller.get_company(user_id)
        return self.display_application_details(designer, company)

    def display_application_details(self, designer, company):
        return render_template("admin/application_detail.html", designer=designer, company = company)

    def _to_list(self):
        return redirect(url_for("admin.view_id_applications"))

    def _to_details(self, user_id):
        return redirect(url_for("admin.view_application_details", user_id=user_id))

    def approve_application(self, user_id):
        if request.method == "GET":
            return self._show_confirm(user_id, "approve")
        controller = ApproveApplicationController()
        if controller.approve_application(user_id):
            self.display_success(f"Application approved for {controller.designer.name}")
        else:
            for err in controller.errors:
                self.display_error(err)
        return self._to_list()

    def reject_application(self, user_id):
        if request.method == "GET":
            return self._show_confirm(user_id, "reject")
        controller = RejectApplicationController()
        if controller.reject_application(user_id):
            self.display_success(f"Application rejected for {controller.designer.name}")
        else:
            for err in controller.errors:
                self.display_error(err)
        return self._to_list()

    def display_confirm(self, designer, action):
        return render_template("admin/confirm_actions.html", designer=designer, action=action)

    def _show_confirm(self, user_id, action):
        controller = ViewApplicationController()
        designer = controller.get_application(user_id)
        if designer is None:
            for err in controller.errors:
                self.display_error(err)
            return self._to_list()
        return self.display_confirm(designer, action)

    def display_success(self, msg):
        flash(msg, "success")
    
    def display_error(self, msg):
        flash(msg, "error")

page = ApplicationReviewPage()


@bp.route("/")
@admin_only
def view_id_applications():
    return page.view_id_applications()


@bp.route("/<int:user_id>")
@admin_only
def view_application_details(user_id):
    return page.view_application_details(user_id)


@bp.route("/<int:user_id>/approve", methods=["GET", "POST"])
@admin_only
def approve_application(user_id):
    return page.approve_application(user_id)


@bp.route("/<int:user_id>/reject", methods=["GET", "POST"])
@admin_only
def reject_application(user_id):
    return page.reject_application(user_id)


@bp.route("/<int:user_id>/request-docs", methods=["POST"])
@admin_only
def request_additional_docs(user_id):
    return page.request_additional_docs(user_id)