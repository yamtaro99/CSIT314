from app.entity.customer_review import CustomerReview


class ReviewController:
    def __init__(self):
        self.errors = []

    def get_pending_reviews(self, designer_id):
        return CustomerReview.find_pending_by_designer(designer_id)

    def get_review_details(self, review_id, designer_id):
        review = CustomerReview.find_by_id(review_id)
        if review is None or review.designer_id != designer_id:
            self.errors.append("The review can no longer be loaded or does not exist.")
            return None
        return review

    def approve_review(self, review_id, designer_id):
        review = self.get_review_details(review_id, designer_id)
        if not review:
            return False
        return review.set_status("approved")

    def reject_review(self, review_id, designer_id):
        review = self.get_review_details(review_id, designer_id)
        if not review:
            return False
        return review.set_status("rejected")

    def get_approved_reviews(self):
        return CustomerReview.find_approved()
