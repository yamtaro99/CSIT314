from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from app.boundary.session import login_required
from app.control.review_controllers import ReviewController
from app.entity.user_account import UserAccount

bp = Blueprint("reviews", __name__, url_prefix="/reviews")
designer_only = login_required(UserAccount.INTERIOR_DESIGNER)

def display_success(msg):
    flash(msg, "success")

def display_error(msg):
    flash(msg, "error")

@bp.route("/pending", methods=["GET"])
@designer_only
def view_pending_reviews():
    """Step 1 & 2: ID views pending reviews list[cite: 36]."""
    controller = ReviewController()
    reviews = controller.get_pending_reviews(g.user.user_id)
    return render_template("reviews/pending_reviews.html", reviews=reviews)

@bp.route("/<int:review_id>", methods=["GET"])
@designer_only
def view_review_details(review_id):
    """Step 3: Show review details (rating, comment, customer)[cite: 36]."""
    controller = ReviewController()
    review = controller.get_review_details(review_id)
    if not review:
        for err in controller.errors:
            display_error(err)
        return redirect(url_for("reviews.view_pending_reviews"))
    return render_template("reviews/review_detail.html", review=review)

@bp.route("/<int:review_id>/approve", methods=["POST"])
@designer_only
def approve_review(review_id):
    """Steps 4, 5 & 6: Approve review and publish[cite: 36]."""
    controller = ReviewController()
    if controller.approve_review(review_id):
        display_success("Review approved and published successfully.")
    else:
        for err in controller.errors:
            display_error(err)
    return redirect(url_for("reviews.view_pending_reviews"))

@bp.route("/<int:review_id>/reject", methods=["POST"])
@designer_only
def reject_review(review_id):
    """Alternative flow 4a: Reject review, keeping it hidden[cite: 36]."""
    controller = ReviewController()
    if controller.reject_review(review_id):
        display_success("Review rejected and kept hidden.")
    else:
        for err in controller.errors:
            display_error(err)
    return redirect(url_for("reviews.view_pending_reviews"))

@bp.route("/approved", methods=["GET"])
def view_approved_reviews():
    """Public page listing all approved reviews for customers to read."""
    controller = ReviewController()
    reviews = controller.get_approved_reviews()
    average = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else None
    return render_template("reviews/approved_reviews.html", reviews=reviews, average=average)

