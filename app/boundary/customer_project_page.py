from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.boundary.session import login_required
from app.control.customer_project_controllers import (ViewProjectDetailsController, ReportProjectController,)
from app.entity.project import Project
from app.entity.project_report import ProjectReport
from app.entity.user_account import UserAccount


# set up the customer project pages and only allow customers to access them
bp = Blueprint("customer_projects", __name__, url_prefix="/projects")
customer_only = login_required(UserAccount.CUSTOMER)


# display error message
def display_error(msg):
    flash(msg, "error")


# UC31 View Project Details

# display the selected project and the related information
def display_project_details(project):
    return render_template(
        "customer_projects/detail.html",
        project=project,
        **project.get_details()
    )


# get the available projects and display them for customers to browse
@bp.route("/")
@customer_only
def display_project_listing():
    projects = Project.find_available_projects()
    return render_template(
        "customer_projects/browse.html",
        projects=projects
    )

# check if the selected project is available before showing the details
@bp.route("/<int:project_id>")
@customer_only
def view_project_details(project_id):
    controller = ViewProjectDetailsController()
    project = controller.get_project_details(project_id)

    # return to the project listing if the project is unavailable
    if project is None:
        display_error("Project unavailable")
        return redirect(
            url_for("customer_projects.display_project_listing")
        )
    
    return display_project_details(project)


# UC37 Report Inappropriate Projects

# display message so that customers know if the report was submitted
def display_report_result(success):
    if success:
        flash("Report submitted successfully", "success")
    else:
        display_error("Unable to submit report. Please try again.")


# open the report form for the selected project
@bp.route("/<int:project_id>/report", methods=["GET"])
@customer_only
def display_report_form(project_id):
    controller = ViewProjectDetailsController()
    project = controller.get_project_details(project_id)

    # do not open the report form if the project is unavailable
    if project is None:
        display_error("Project unavailable")
        return redirect(
            url_for("customer_projects.display_project_listing")
        )

    return render_template(
        "customer_projects/report.html",
        project=project,
        reasons=ProjectReport.VALID_REASONS,
        reason="",
        details=""
    )

# get customers' report details and pass them back to the controller
@bp.route("/<int:project_id>/report", methods=["POST"])
@customer_only
def submit_report(project_id):
    reason = request.form.get("reason", "")
    details = request.form.get("details", "")

    controller = ReportProjectController()

    # display success message if the report is valid and saved
    if controller.report_project(
        g.user.user_id, project_id, reason, details
    ):
        display_report_result(True)
        return redirect(
            url_for("customer_projects.view_project_details", project_id=project_id)
        )

    # return to the project listing if the project is no longer available
    if "Project unavailable" in controller.errors:
        display_error("Project unavailable")
        return redirect(
            url_for("customer_projects.display_project_listing")
        )

    project = ViewProjectDetailsController().get_project_details(project_id)

    # show the errors and keep the entered details so that customers can try again
    for error in controller.errors:
        display_error(error)

    return render_template(
        "customer_projects/report.html",
        project=project,
        reasons=ProjectReport.VALID_REASONS,
        reason=reason,
        details=details
    ), 400

# cancel the report and return to project details without saving anything
@bp.route("/<int:project_id>/report/cancel", methods=["POST"])
@customer_only
def cancel_report(project_id):
    return redirect(
        url_for("customer_projects.view_project_details", project_id=project_id)
    )