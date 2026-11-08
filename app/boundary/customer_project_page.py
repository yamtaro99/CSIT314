from flask import Blueprint, flash, redirect, render_template, url_for

from app.boundary.session import login_required
from app.control.customer_project_controllers import ViewProjectDetailsController
from app.entity.project import Project
from app.entity.user_account import UserAccount


bp = Blueprint("customer_projects", __name__, url_prefix="/projects")
customer_only = login_required(UserAccount.CUSTOMER)


def display_error(msg):
    flash(msg, "error")


def display_project_details(project):
    return render_template(
        "customer_projects/detail.html",
        project=project,
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
    
    return display_project_details(project)