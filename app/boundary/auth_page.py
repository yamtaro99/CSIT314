from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.boundary.session import load_logged_in_user
from app.control.login_controller import LoginController

bp = Blueprint("auth", __name__)
bp.before_app_request(load_logged_in_user)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        controller = LoginController()
        account = controller.login(request.form.get("email"), request.form.get("password"))
        if account is None:
            flash(controller.error, "error")
        else:
            session.clear()
            session["user_id"] = account.user_id
            next_url = request.args.get("next", "")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("home.index")
            return redirect(next_url)
    return render_template("auth/login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out", "success")
    return redirect(url_for("auth.login"))
