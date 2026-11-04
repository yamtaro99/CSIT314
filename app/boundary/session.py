from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

from app.entity.user_account import UserAccount


def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = UserAccount.find_by_id(user_id) if user_id else None
    if g.user is not None and not g.user.is_active():
        session.clear()
        g.user = None


def login_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                flash("Please log in first", "error")
                return redirect(url_for("auth.login", next=request.path))
            if roles and g.user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator
