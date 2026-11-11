from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app.boundary.session import login_required
from app.control.customer_project_controllers import (ViewProjectDetailsController, ReportProjectController,)
from app.control.project_interest_controllers import TrackProjectShortlistController, ViewFavouritesController
from app.entity.project_shortlist import ProjectShortlist
from app.entity.project_view import ProjectView
from app.entity.project import Project
from app.entity.project_report import ProjectReport
from app.entity.user_account import UserAccount


bp = Blueprint("customer_projects", __name__, url_prefix="/projects")
customer_only = login_required(UserAccount.CUSTOMER)


def display_error(msg):
    flash(msg, "error")


# UC31 View Project Details

def display_project_details(project, shortlisted):
    return render_template(
        "customer_projects/detail.html",
        project=project,
        shortlisted=shortlisted,
        **project.get_details()
    )


@bp.route("/")
@customer_only
def display_project_listing():
    projects = Project.find_available_projects()
    return render_template(
        "customer_projects/browse.html",
        projects=projects
    )

@bp.route("/<int:project_id>")
@customer_only
def view_project_details(project_id):
    controller = ViewProjectDetailsController()
    project = controller.get_project_details(project_id)

    if project is None:
        display_error("Project unavailable")
        return redirect(
            url_for("customer_projects.display_project_listing")
        )
    
    ProjectView.record(g.user.user_id, project.project_id)
    return display_project_details(
        project, ProjectShortlist.is_saved(g.user.user_id, project.project_id)
    )


# Supporting favourites behavior, shared by the customer's My Favourites page and US03.
@bp.route("/favourites")
@customer_only
def my_favourites():
    favourites = ViewFavouritesController().get_favourites(g.user.user_id)
    if favourites is None:
        return ("Forbidden", 403)
    return render_template("customer_projects/favourites.html", projects=favourites)


# A customer saves or removes an available project; the designer sees the count via US03.
@bp.route("/<int:project_id>/shortlist", methods=["POST"])
@customer_only
def update_shortlist(project_id):
    controller = TrackProjectShortlistController()
    if controller.set_shortlisted(g.user.user_id, project_id, request.form.get("action")):
        if controller.result == "added":
            flash("Project added to your shortlist", "success")
        elif controller.result == "removed":
            flash("Project removed from your shortlist", "success")
        else:
            flash("Your shortlist is already up to date", "success")
        if request.form.get("return_to") == "favourites":
            return redirect(url_for("customer_projects.my_favourites"))
        return redirect(url_for("customer_projects.view_project_details", project_id=project_id))

    for error in controller.errors:
        display_error(error)
    if "Project unavailable" in controller.errors:
        return redirect(url_for("customer_projects.display_project_listing"))
    return redirect(url_for("customer_projects.view_project_details", project_id=project_id))


# UC37 Report Inappropriate Projects

@bp.route("/<int:project_id>/report", methods=["GET"])
@customer_only
def display_report_form(project_id):
    controller = ViewProjectDetailsController()
    project = controller.get_project_details(project_id)

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

@bp.route("/<int:project_id>/report", methods=["POST"])
@customer_only
def submit_report(project_id):
    reason = request.form.get("reason", "")
    details = request.form.get("details", "")

    controller = ReportProjectController()

    if controller.report_project(
        g.user.user_id, project_id, reason, details
    ):
        flash("Report submitted successfully", "success")
        return redirect(
            url_for("customer_projects.view_project_details", project_id=project_id)
        )

    if "Project unavailable" in controller.errors:
        display_error("Project unavailable")
        return redirect(
            url_for("customer_projects.display_project_listing")
        )

    project = ViewProjectDetailsController().get_project_details(project_id)

    for error in controller.errors:
        display_error(error)

    return render_template(
        "customer_projects/report.html",
        project=project,
        reasons=ProjectReport.VALID_REASONS,
        reason=reason,
        details=details
    ), 400

@bp.route("/<int:project_id>/report/cancel", methods=["POST"])
@customer_only
def cancel_report(project_id):
    return redirect(
        url_for("customer_projects.view_project_details", project_id=project_id)
    )
