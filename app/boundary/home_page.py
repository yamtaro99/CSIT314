from flask import Blueprint, render_template

from app.boundary.session import login_required

bp = Blueprint("home", __name__)


@bp.route("/")
@login_required()
def index():
    return render_template("home.html")
