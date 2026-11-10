from app.entity.customer_review import CustomerReview


class ReviewController:
    def __init__(self):
        self.errors = []

    def get_pending_reviews(self, designer_id):
        """Step 1: System alerts/fetches reviews waiting for approval."""
        return CustomerReview.find_pending_by_designer(designer_id)

    def get_review_details(self, review_id, designer_id):
        """Steps 2 & 3: Fetch review details for the logged-in designer only.

        A review that belongs to another designer is reported the same way as a
        missing review, so the error doesn't reveal that the review exists.
        """
        review = CustomerReview.find_by_id(review_id)
        if review is None or review.designer_id != designer_id:
            self.errors.append("The review can no longer be loaded or does not exist.")
            return None
        return review

    def approve_review(self, review_id, designer_id):
        """Steps 4, 5 & 6: Set status to approved and publish, for the logged-in designer only."""
        review = self.get_review_details(review_id, designer_id)
        if not review:
            return False
        return review.set_status("approved")

    def reject_review(self, review_id, designer_id):
        """Alternative flow 4a: Set status to rejected, for the logged-in designer only."""
        review = self.get_review_details(review_id, designer_id)
        if not review:
            return False
        return review.set_status("rejected")

    def get_approved_reviews(self):
        """Returns all approved reviews to be shown publicly."""
        return CustomerReview.find_approved()