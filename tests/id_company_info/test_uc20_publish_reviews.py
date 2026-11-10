import pytest

from app.control.review_controllers import ReviewController
from app.db import get_db
from app.entity.customer_review import CustomerReview
from app.entity.user_account import UserAccount
from tests.conftest import login, make_user


# ---------- local helpers (review setup and DB reads) ----------

def insert_review(app, designer_id, comment, status="pending", rating=5,
                  submitted_at="2026-11-08T14:18:36"):
    with app.app_context():
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO customer_review (designer_id, customer_id, rating, comment, status, submitted_at)"
            " VALUES (?, NULL, ?, ?, ?, ?)",
            (designer_id, rating, comment, status, submitted_at),
        )
        conn.commit()
        return cur.lastrowid


def review_status(app, review_id):
    with app.app_context():
        row = get_db().execute(
            "SELECT status FROM customer_review WHERE review_id = ?", (review_id,)
        ).fetchone()
        return row["status"] if row else None


@pytest.fixture
def designer_client(client, designer):
    login(client, designer.email)
    return client


# ---------- Entity: CustomerReview ----------

class TestCustomerReviewEntity:

    def test_find_pending_returns_only_this_designers_pending_reviews(self, app, designer, other_designer):
        insert_review(app, designer.user_id, "Mine, pending", status="pending")
        insert_review(app, designer.user_id, "Mine, approved", status="approved")
        insert_review(app, other_designer.user_id, "Theirs, pending", status="pending")

        with app.app_context():
            reviews = CustomerReview.find_pending_by_designer(designer.user_id)
            assert [r.comment for r in reviews] == ["Mine, pending"]

    def test_find_by_id_formats_submitted_date(self, app, designer):
        review_id = insert_review(app, designer.user_id, "Great", submitted_at="2026-11-08T14:18:36")

        with app.app_context():
            review = CustomerReview.find_by_id(review_id)
            assert review.submittedAt == "08 Nov 2026, 14:18"

    def test_find_by_id_returns_none_for_missing_review(self, app):
        with app.app_context():
            assert CustomerReview.find_by_id(9999) is None

    def test_find_approved_returns_only_approved_with_designer_name(self, app, designer):
        insert_review(app, designer.user_id, "Shown", status="approved")
        insert_review(app, designer.user_id, "Hidden pending", status="pending")
        insert_review(app, designer.user_id, "Hidden rejected", status="rejected")

        with app.app_context():
            reviews = CustomerReview.find_approved()
            assert [r.comment for r in reviews] == ["Shown"]
            assert reviews[0].designer_name == designer.name

    def test_find_approved_is_newest_first(self, app, designer):
        insert_review(app, designer.user_id, "Older", status="approved", submitted_at="2026-11-01T10:00:00")
        insert_review(app, designer.user_id, "Newer", status="approved", submitted_at="2026-11-07T10:00:00")

        with app.app_context():
            assert [r.comment for r in CustomerReview.find_approved()] == ["Newer", "Older"]


# ---------- Control: ReviewController ----------

class TestReviewController:

    def test_approve_sets_status_to_approved(self, app, designer):
        review_id = insert_review(app, designer.user_id, "Good work")

        with app.app_context():
            controller = ReviewController()
            assert controller.approve_review(review_id, designer.user_id) is True
            assert controller.errors == []
        assert review_status(app, review_id) == "approved"

    def test_reject_sets_status_to_rejected(self, app, designer):
        review_id = insert_review(app, designer.user_id, "Poor work")

        with app.app_context():
            assert ReviewController().reject_review(review_id, designer.user_id) is True
        assert review_status(app, review_id) == "rejected"

    def test_approving_missing_review_fails_with_error(self, app, designer):
        with app.app_context():
            controller = ReviewController()
            assert controller.approve_review(9999, designer.user_id) is False
            assert controller.errors == ["The review can no longer be loaded or does not exist."]

    def test_get_review_details_returns_none_for_missing_review(self, app, designer):
        with app.app_context():
            controller = ReviewController()
            assert controller.get_review_details(9999, designer.user_id) is None
            assert "The review can no longer be loaded or does not exist." in controller.errors

    def test_get_pending_reviews_lists_only_pending(self, app, designer):
        insert_review(app, designer.user_id, "Pending one", status="pending")
        insert_review(app, designer.user_id, "Already approved", status="approved")

        with app.app_context():
            reviews = ReviewController().get_pending_reviews(designer.user_id)
            assert [r.comment for r in reviews] == ["Pending one"]


# ---------- Route: designer's pending list and detail ----------

class TestDesignerReviewPages:

    def test_pending_list_shows_this_designers_pending_reviews(self, designer_client, app, designer, other_designer):
        insert_review(app, designer.user_id, "Mine to review")
        insert_review(app, other_designer.user_id, "Not mine")

        response = designer_client.get("/reviews/pending")

        assert response.status_code == 200
        assert b"Mine to review" in response.data
        assert b"Not mine" not in response.data

    def test_pending_list_empty_message(self, designer_client):
        response = designer_client.get("/reviews/pending")

        assert b"No pending customer reviews waiting for approval." in response.data

    def test_detail_page_shows_rating_comment_and_formatted_date(self, designer_client, app, designer):
        review_id = insert_review(app, designer.user_id, "Lovely carpentry", rating=3,
                                  submitted_at="2026-11-08T14:18:36")

        response = designer_client.get(f"/reviews/{review_id}")

        assert response.status_code == 200
        assert b"Lovely carpentry" in response.data
        assert b"3 / 5 Stars" in response.data
        assert b"08 Nov 2026, 14:18" in response.data

    def test_detail_page_for_missing_review_redirects_with_error(self, designer_client):
        response = designer_client.get("/reviews/9999", follow_redirects=True)

        assert b"The review can no longer be loaded or does not exist." in response.data


# ---------- Route: approve and reject ----------

class TestApproveRejectRoutes:

    def test_approve_publishes_review_and_returns_to_pending_list(self, designer_client, app, designer):
        review_id = insert_review(app, designer.user_id, "Publish me")

        response = designer_client.post(f"/reviews/{review_id}/approve", follow_redirects=True)

        assert b"Review approved and published successfully." in response.data
        assert review_status(app, review_id) == "approved"
        assert b"Publish me" not in response.data  # cleared from the pending list

    def test_reject_keeps_review_hidden(self, designer_client, app, designer):
        review_id = insert_review(app, designer.user_id, "Reject me")

        response = designer_client.post(f"/reviews/{review_id}/reject", follow_redirects=True)

        assert b"Review rejected and kept hidden." in response.data
        assert review_status(app, review_id) == "rejected"
        assert b"Reject me" not in response.data

    def test_approving_missing_review_shows_error(self, designer_client):
        response = designer_client.post("/reviews/9999/approve", follow_redirects=True)

        assert b"The review can no longer be loaded or does not exist." in response.data

    def test_review_stays_pending_if_it_cannot_be_loaded(self, designer_client, app, designer):
        review_id = insert_review(app, designer.user_id, "Still here")

        # Exception 3a: the review can't be loaded, so nothing changes
        designer_client.post("/reviews/9999/approve")

        assert review_status(app, review_id) == "pending"

    def test_designer_cannot_approve_another_designers_review(self, client, app, designer, other_designer):
        review_id = insert_review(app, other_designer.user_id, "Not yours")
        login(client, designer.email)

        client.post(f"/reviews/{review_id}/approve")

        assert review_status(app, review_id) == "pending"

    def test_designer_cannot_reject_another_designers_review(self, client, app, designer, other_designer):
        review_id = insert_review(app, other_designer.user_id, "Not yours")
        login(client, designer.email)

        client.post(f"/reviews/{review_id}/reject")

        assert review_status(app, review_id) == "pending"


# ---------- Public page: what visitors see ----------

class TestPublicApprovedReviewsPage:

    def test_visitor_does_not_need_to_log_in(self, client):
        response = client.get("/reviews/approved")

        assert response.status_code == 200

    def test_shows_approved_reviews_only(self, client, app, designer):
        insert_review(app, designer.user_id, "Published comment", status="approved")
        insert_review(app, designer.user_id, "Pending comment", status="pending")
        insert_review(app, designer.user_id, "Rejected comment", status="rejected")

        response = client.get("/reviews/approved")

        assert b"Published comment" in response.data
        assert b"Pending comment" not in response.data
        assert b"Rejected comment" not in response.data

    def test_shows_designer_name_and_formatted_date(self, client, app, designer):
        insert_review(app, designer.user_id, "Named", status="approved", submitted_at="2026-11-08T14:18:36")

        response = client.get("/reviews/approved")

        assert f"for {designer.name}".encode() in response.data
        assert b"08 Nov 2026, 14:18" in response.data

    def test_shows_average_rating(self, client, app, designer):
        insert_review(app, designer.user_id, "Five", status="approved", rating=5)
        insert_review(app, designer.user_id, "Three", status="approved", rating=3)

        response = client.get("/reviews/approved")

        assert b"Average rating:" in response.data
        assert b"4.0 / 5 from 2 reviews" in response.data

    def test_empty_message_when_nothing_published(self, client):
        response = client.get("/reviews/approved")

        assert b"No Customer reviews have been published yet." in response.data


# ---------- Access control ----------

class TestAccessControl:

    def test_anonymous_user_is_redirected_from_pending_list(self, client):
        response = client.get("/reviews/pending")

        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_customer_cannot_open_pending_list(self, client):
        make_user(UserAccount.CUSTOMER, "c@test.local")
        login(client, "c@test.local")

        assert client.get("/reviews/pending").status_code == 403

    def test_customer_cannot_approve_a_review(self, client, app, designer):
        review_id = insert_review(app, designer.user_id, "Customer tries")
        make_user(UserAccount.CUSTOMER, "c@test.local")
        login(client, "c@test.local")

        assert client.post(f"/reviews/{review_id}/approve").status_code == 403
        assert review_status(app, review_id) == "pending"

    def test_anonymous_user_cannot_approve_a_review(self, client, app, designer):
        review_id = insert_review(app, designer.user_id, "Anonymous tries")

        response = client.post(f"/reviews/{review_id}/approve")

        assert response.status_code == 302
        assert review_status(app, review_id) == "pending"


# ---------- Ownership: a designer can only open their own reviews ----------

class TestOwnership:

    def test_detail_page_for_another_designers_review_is_refused(self, designer_client, app, other_designer):
        review_id = insert_review(app, other_designer.user_id, "Not yours")

        response = designer_client.get(f"/reviews/{review_id}", follow_redirects=True)

        assert b"The review can no longer be loaded or does not exist." in response.data
        assert b"Not yours" not in response.data