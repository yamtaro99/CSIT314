from app.entity.customer_review import CustomerReview

class ReviewController:
    def __init__(self):
        self.errors = []

    def get_pending_reviews(self, designer_id):
        """Step 1: System alerts/fetches reviews waiting for approval[cite: 36]."""
        return CustomerReview.find_pending_by_designer(designer_id)

    def get_review_details(self, review_id):
        """Step 2 & 3: Fetch review details; handles Exception 3a if review can no longer be loaded[cite: 36]."""
        review = CustomerReview.find_by_id(review_id)
        if review is None:
            self.errors.append("The review can no longer be loaded or does not exist.")
            return None
        return review

    def approve_review(self, review_id):
        """Steps 4, 5 & 6: Set status to approved and publish[cite: 36]."""
        review = self.get_review_details(review_id)
        if not review:
            return False
        return review.set_status("approved")

    def reject_review(self, review_id):
        """Alternative flow 4a: Set status to rejected, review stays hidden[cite: 36]."""
        review = self.get_review_details(review_id)
        if not review:
            return False
        return review.set_status("rejected")

    def get_approved_reviews(self):
        """Returns all approved reviews to be shown publicly."""
        return CustomerReview.find_approved()