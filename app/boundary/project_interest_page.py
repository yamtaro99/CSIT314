from flask import Blueprint, abort, g, render_template, request
from app.boundary.session import login_required
from app.control.project_interest_controllers import (
    ViewShortlistCountsController, ViewWeeklyInterestTrendsController,
)
from app.entity.user_account import UserAccount

bp = Blueprint("project_interest", __name__, url_prefix="/interest")
designer_only = login_required(UserAccount.INTERIOR_DESIGNER)


@bp.route("/")
@designer_only
def dashboard():
    counts = ViewShortlistCountsController().get_counts(g.user.user_id)
    if counts is None:
        abort(403)
    raw_project_id = request.args.get("project_id", "all")
    if raw_project_id == "all":
        selected_id = None
    else:
        try:
            selected_id = int(raw_project_id)
        except (TypeError, ValueError):
            abort(400)
    trend_controller = ViewWeeklyInterestTrendsController()
    trend = trend_controller.get_trends(g.user.user_id, selected_id)
    if trend is None:
        abort(404 if "Project unavailable" in trend_controller.errors else 403)
    return render_template(
        "project_interest/dashboard.html",
        metrics=counts, trend=trend, selected_project_id=selected_id,
    )
