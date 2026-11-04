from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from app.boundary.session import login_required
from app.control.portfolio_controllers import (
    AddProjectController,
    RemoveProjectController,
    TagProjectController,
    UpdateProjectController,
    UploadPhotoController,
)
from app.entity.portfolio import Portfolio
from app.entity.user_account import UserAccount

bp = Blueprint("portfolio", __name__, url_prefix="/portfolio")
designer_only = login_required(UserAccount.INTERIOR_DESIGNER)


def display_success(msg):
    flash(msg, "success")


def display_error(msg):
    flash(msg, "error")


def _own_project_or_404(project_id):
    project = Portfolio(g.user.user_id).get_project(project_id)
    if project is None:
        abort(404)
    return project


def _project_form_fields():
    return {f: request.form.get(f, "") for f in ("title", "description", "location", "completion_date")}


@bp.route("/")
@designer_only
def display_portfolio():
    projects = Portfolio(g.user.user_id).get_projects()
    return render_template("portfolio/portfolio.html", projects=projects)


@bp.route("/add", methods=["GET", "POST"])
@designer_only
def display_add_project_form():
    form = _project_form_fields()
    if request.method == "POST":
        controller = AddProjectController()
        if controller.add_project(g.user.user_id, **form):
            display_success("Project added")
            return redirect(url_for("portfolio.display_project", project_id=controller.project.project_id))
        for err in controller.errors:
            display_error(err)
    return render_template("portfolio/project_form.html", form=form, project=None)


@bp.route("/<int:project_id>")
@designer_only
def display_project(project_id):
    project = _own_project_or_404(project_id)
    return render_template("portfolio/project_detail.html", project=project,
                           photos=project.get_photos(), categories=project.get_categories())


@bp.route("/<int:project_id>/edit", methods=["GET", "POST"])
@designer_only
def display_edit_project_form(project_id):
    project = _own_project_or_404(project_id)
    if request.method == "POST":
        form = _project_form_fields()
        controller = UpdateProjectController()
        if controller.update_project(project_id, form, g.user.user_id):
            display_success("Project updated")
            return redirect(url_for("portfolio.display_project", project_id=project_id))
        for err in controller.errors:
            display_error(err)
    else:
        form = {f: getattr(project, f) for f in ("title", "description", "location", "completion_date")}
    return render_template("portfolio/project_form.html", form=form, project=project)


@bp.route("/<int:project_id>/photos", methods=["GET", "POST"])
@designer_only
def display_upload_form(project_id):
    project = _own_project_or_404(project_id)
    if request.method == "POST":
        controller = UploadPhotoController()
        ok = controller.upload_photos(project_id, request.files.getlist("photos"), g.user.user_id)
        for err in controller.errors:
            display_error(err)
        if ok:
            display_success(f"{controller.saved_count} photo(s) uploaded")
            return redirect(url_for("portfolio.display_project", project_id=project_id))
    return render_template("portfolio/upload_photos.html", project=project)


@bp.route("/<int:project_id>/categories", methods=["GET", "POST"])
@designer_only
def display_category_selector(project_id):
    project = _own_project_or_404(project_id)
    controller = TagProjectController()
    if request.method == "POST":
        if controller.tag_project(project_id, request.form.getlist("category_ids"), g.user.user_id):
            display_success("Categories updated")
            return redirect(url_for("portfolio.display_project", project_id=project_id))
        for err in controller.errors:
            display_error(err)
    selected = {c.category_id for c in project.get_categories()}
    return render_template("portfolio/categories.html", project=project,
                           categories=controller.get_categories(), selected=selected)


@bp.route("/<int:project_id>/remove", methods=["GET", "POST"])
@designer_only
def confirm_remove_project(project_id):
    project = _own_project_or_404(project_id)
    if request.method == "POST":
        if RemoveProjectController().remove_project(project_id, g.user.user_id):
            display_success("Project removed")
        else:
            display_error("Could not remove the project")
        return redirect(url_for("portfolio.display_portfolio"))
    return render_template("portfolio/confirm_remove.html", project=project)
