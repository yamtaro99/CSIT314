from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.boundary.session import login_required
from app.control.platform_mgmt_controllers import (
    CategoryController,
    DesignerPerformanceController,
    IDPQueueController,
    PlatformDashboardController,
    PlatformSettingsController,
    ReportsController,
    UserManagementController,
)
from app.entity.user_account import UserAccount

bp = Blueprint("platform_mgmt", __name__, url_prefix="/platform")
pm_only = login_required(UserAccount.PLATFORM_MANAGER)


class PlatformMgmtPage:
    def __init__(self):
        self.dashboard_ctrl = PlatformDashboardController()
        self.category_ctrl = CategoryController()
        self.user_ctrl = UserManagementController()
        self.idp_ctrl = IDPQueueController()
        self.reports_ctrl = ReportsController()
        self.designer_perf_ctrl = DesignerPerformanceController()
        self.settings_ctrl = PlatformSettingsController()

    def dashboard(self):
        metrics = self.dashboard_ctrl.get_metrics()
        if self.dashboard_ctrl.errors:
            for err in self.dashboard_ctrl.errors:
                flash(err, "error")
        return render_template("platform_mgmt/dashboard.html", metrics=metrics)

    def categories(self):
        cats = self.category_ctrl.get_all_categories()
        return render_template("platform_mgmt/categories.html", categories=cats)

    def create_category(self):
        if request.method == "GET":
            return render_template("platform_mgmt/category_form.html", category=None, action="Create")

        name = request.form.get("name", "").strip()
        is_active = request.form.get("is_active")

        cat = self.category_ctrl.create_category(name, is_active)
        if cat:
            flash(f"Category '{cat.name}' created successfully", "success")
            return redirect(url_for("platform_mgmt.categories"))

        for err in self.category_ctrl.errors:
            flash(err, "error")
        return render_template("platform_mgmt/category_form.html",
                               category={"name": name, "is_active": bool(is_active) if is_active else False},
                               action="Create")

    def edit_category(self, category_id):
        if request.method == "GET":
            conn = __import__("app.db", fromlist=["get_db"]).get_db()
            row = conn.execute("SELECT * FROM category WHERE category_id = ?", (category_id,)).fetchone()
            if not row:
                flash("Category not found", "error")
                return redirect(url_for("platform_mgmt.categories"))
            cat = {"category_id": row["category_id"], "name": row["name"], "is_active": bool(row["is_active"])}
            return render_template("platform_mgmt/category_form.html", category=cat, action="Edit")

        name = request.form.get("name", "").strip()
        is_active = request.form.get("is_active")

        if self.category_ctrl.update_category(category_id, name, is_active):
            flash(f"Category updated successfully", "success")
            return redirect(url_for("platform_mgmt.categories"))

        for err in self.category_ctrl.errors:
            flash(err, "error")
        return render_template("platform_mgmt/category_form.html",
                               category={"category_id": category_id, "name": name, "is_active": bool(is_active) if is_active else False},
                               action="Edit")

    def delete_category(self, category_id):
        if request.method == "GET":
            conn = __import__("app.db", fromlist=["get_db"]).get_db()
            row = conn.execute("SELECT * FROM category WHERE category_id = ?", (category_id,)).fetchone()
            if not row:
                flash("Category not found", "error")
                return redirect(url_for("platform_mgmt.categories"))
            cat = {"category_id": row["category_id"], "name": row["name"]}
            return render_template("platform_mgmt/category_confirm_delete.html", category=cat)

        result = self.category_ctrl.delete_category(category_id)
        if result == "deleted":
            flash("Category deleted permanently", "success")
        elif result == "deactivated":
            flash("Category is in use by active projects; deactivated instead", "warning")
        else:
            for err in self.category_ctrl.errors:
                flash(err, "error")
        return redirect(url_for("platform_mgmt.categories"))

    def users(self):
        role_filter = request.args.get("role") or None
        status_filter = request.args.get("status") or None
        search = request.args.get("search") or None
        page = max(1, int(request.args.get("page", 1)))

        result = self.user_ctrl.get_users(role_filter, status_filter, search, page)

        return render_template("platform_mgmt/users.html",
                               users=result["users"],
                               pagination=result,
                               role_filter=role_filter,
                               status_filter=status_filter,
                               search=search,
                               role_options=self.user_ctrl.get_role_options(),
                               status_options=self.user_ctrl.get_status_options())

    def user_detail(self, user_id):
        detail = self.user_ctrl.get_user_detail(user_id)
        if not detail:
            flash("User not found", "error")
            return redirect(url_for("platform_mgmt.users"))
        return render_template("platform_mgmt/user_detail.html", **detail)

    def update_user_status(self, user_id):
        if request.method == "POST":
            new_status = request.form.get("status")
            if self.user_ctrl.update_user_status(user_id, new_status):
                flash(f"User status updated to {new_status}", "success")
            else:
                for err in self.user_ctrl.errors:
                    flash(err, "error")
        return redirect(url_for("platform_mgmt.user_detail", user_id=user_id))

    def idp_queue(self):
        page = max(1, int(request.args.get("page", 1)))
        result = self.idp_ctrl.get_pending_projects(page)
        return render_template("platform_mgmt/idp_queue.html",
                               projects=result["projects"],
                               pagination=result)

    def idp_detail(self, project_id):
        project = self.idp_ctrl.get_project_detail(project_id)
        if not project:
            flash("Project not found", "error")
            return redirect(url_for("platform_mgmt.idp_queue"))
        return render_template("platform_mgmt/idp_detail.html", project=project)

    def idp_approve(self, project_id):
        if request.method == "POST":
            if self.idp_ctrl.approve_project(project_id):
                flash("Project approved and published", "success")
            else:
                for err in self.idp_ctrl.errors:
                    flash(err, "error")
        return redirect(url_for("platform_mgmt.idp_queue"))

    def idp_reject(self, project_id):
        if request.method == "POST":
            if self.idp_ctrl.reject_project(project_id):
                flash("Project rejected", "success")
            else:
                for err in self.idp_ctrl.errors:
                    flash(err, "error")
        return redirect(url_for("platform_mgmt.idp_queue"))

    def reports(self):
        return render_template("platform_mgmt/reports.html")

    def daily_report(self):
        date = request.args.get("date")
        report = self.reports_ctrl.get_daily_report(date)
        if self.reports_ctrl.errors:
            for err in self.reports_ctrl.errors:
                flash(err, "error")
        return render_template(
            "platform_mgmt/report_detail.html",
            report=report,
            period_type="daily",
            default_date=date,
        )

    def weekly_report(self):
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        report = self.reports_ctrl.get_weekly_report(start_date, end_date)
        if self.reports_ctrl.errors:
            for err in self.reports_ctrl.errors:
                flash(err, "error")
        return render_template(
            "platform_mgmt/report_detail.html",
            report=report,
            period_type="weekly",
            default_start=start_date,
            default_end=end_date,
        )

    def monthly_report(self):
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        report = self.reports_ctrl.get_monthly_report(start_date, end_date)
        if self.reports_ctrl.errors:
            for err in self.reports_ctrl.errors:
                flash(err, "error")
        return render_template(
            "platform_mgmt/report_detail.html",
            report=report,
            period_type="monthly",
            default_start=start_date,
            default_end=end_date,
        )

    def designer_performance(self):
        designers = self.designer_perf_ctrl.get_all_designers()
        if self.designer_perf_ctrl.errors:
            for err in self.designer_perf_ctrl.errors:
                flash(err, "error")
        return render_template(
            "platform_mgmt/designer_performance.html",
            designers=designers,
        )

    def designer_performance_detail(self, designer_id):
        detail = self.designer_perf_ctrl.get_designer_detail(designer_id)
        if not detail:
            flash("Designer not found", "error")
            return redirect(url_for("platform_mgmt.designer_performance"))
        return render_template(
            "platform_mgmt/designer_performance_detail.html",
            **detail,
        )

    def platform_settings(self):
        if request.method == "GET":
            settings = self.settings_ctrl.get_settings()
            defaults = self.settings_ctrl.get_default_settings()
            for key, info in defaults.items():
                if key not in settings:
                    settings[key] = info
            return render_template(
                "platform_mgmt/platform_settings.html",
                settings=settings,
            )

        updated = self.settings_ctrl.update_settings(request.form)
        if self.settings_ctrl.errors:
            for err in self.settings_ctrl.errors:
                flash(err, "error")
        else:
            if updated:
                flash(f"Settings updated: {', '.join(updated)}", "success")
            else:
                flash("No changes made", "info")
        return redirect(url_for("platform_mgmt.platform_settings"))


page = PlatformMgmtPage()


@bp.route("/")
@pm_only
def dashboard():
    return page.dashboard()


@bp.route("/categories")
@pm_only
def categories():
    return page.categories()


@bp.route("/categories/create", methods=["GET", "POST"])
@pm_only
def create_category():
    return page.create_category()


@bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@pm_only
def edit_category(category_id):
    return page.edit_category(category_id)


@bp.route("/categories/<int:category_id>/delete", methods=["GET", "POST"])
@pm_only
def delete_category(category_id):
    return page.delete_category(category_id)


@bp.route("/users")
@pm_only
def users():
    return page.users()


@bp.route("/users/<int:user_id>")
@pm_only
def user_detail(user_id):
    return page.user_detail(user_id)


@bp.route("/users/<int:user_id>/status", methods=["POST"])
@pm_only
def update_user_status(user_id):
    return page.update_user_status(user_id)


@bp.route("/idp-queue")
@pm_only
def idp_queue():
    return page.idp_queue()


@bp.route("/idp-queue/<int:project_id>")
@pm_only
def idp_detail(project_id):
    return page.idp_detail(project_id)


@bp.route("/idp-queue/<int:project_id>/approve", methods=["POST"])
@pm_only
def idp_approve(project_id):
    return page.idp_approve(project_id)


@bp.route("/idp-queue/<int:project_id>/reject", methods=["POST"])
@pm_only
def idp_reject(project_id):
    return page.idp_reject(project_id)


@bp.route("/reports")
@pm_only
def reports():
    return page.reports()


@bp.route("/reports/daily")
@pm_only
def daily_report():
    return page.daily_report()


@bp.route("/reports/weekly")
@pm_only
def weekly_report():
    return page.weekly_report()


@bp.route("/reports/monthly")
@pm_only
def monthly_report():
    return page.monthly_report()


@bp.route("/designer-performance")
@pm_only
def designer_performance():
    return page.designer_performance()


@bp.route("/designer-performance/<int:designer_id>")
@pm_only
def designer_performance_detail(designer_id):
    return page.designer_performance_detail(designer_id)


@bp.route("/settings", methods=["GET", "POST"])
@pm_only
def platform_settings():
    return page.platform_settings()
