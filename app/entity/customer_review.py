from app.db import get_db, now

class CustomerReview:
    def __init__(self, reviewId, rating, comment, status, submittedAt, designer_id=None, client_id=None):
        self.reviewId = reviewId
        self.rating = rating
        self.comment = comment
        self.status = status  # 'pending', 'approved', 'rejected'
        self.submittedAt = submittedAt
        self.designer_id = designer_id
        self.client_id = client_id

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
            client_id=row["client_id"],
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