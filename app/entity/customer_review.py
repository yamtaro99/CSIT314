from app.db import get_db, now

class CustomerReview:
    def __init__(self, reviewId, rating, comment, status, submittedAt, designer_id=None, customer_id=None):
        self.reviewId = reviewId
        self.rating = rating
        self.comment = comment
        self.status = status  # 'pending', 'approved', 'rejected'
        self.submittedAt = submittedAt
        self.designer_id = designer_id
        self.customer_id = customer_id

    def set_status(self, new_status):
        """Updates the review status ('approved' or 'rejected')."""
        conn = get_db()
        conn.execute(
            "UPDATE customer_review SET status = ? WHERE review_id = ?",
            (new_status, self.reviewId)
        )
        conn.commit()
        self.status = new_status
        return True

    @classmethod
    def _from_row(cls, row):
        return cls(
            reviewId=row["review_id"],
            designer_id=row["designer_id"],
            customer_id=row["customer_id"],
            rating=row["rating"],
            comment=row["comment"],
            status=row["status"],
            submittedAt=row["submitted_at"]
        )

    @classmethod
    def find_pending_by_designer(cls, designer_id):
        rows = get_db().execute(
            "SELECT * FROM customer_review WHERE designer_id = ? AND status = 'pending' ORDER BY submitted_at DESC",
            (designer_id,)
        ).fetchall()
        return [cls._from_row(r) for r in rows]

    @classmethod
    def find_by_id(cls, review_id):
        row = get_db().execute(
            "SELECT * FROM customer_review WHERE review_id = ?",
            (review_id,)
        ).fetchone()
        return cls._from_row(row) if row else None
    
    @classmethod
    def find_approved(cls):
        """Fetches approved reviews, newest first, with the designer's name attached."""
        rows = get_db().execute(
            "SELECT r.*, u.name AS designer_name "
            "FROM customer_review r "
            "LEFT JOIN user_account u ON u.user_id = r.designer_id "
            "WHERE r.status = 'approved' "
            "ORDER BY r.submitted_at DESC"
        ).fetchall()
        reviews = []
        for row in rows:
            review = cls._from_row(row)
            review.designer_name = row["designer_name"]
            reviews.append(review)
        return reviews