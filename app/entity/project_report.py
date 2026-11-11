import sqlite3

from app.db import get_db, now


# UC37 Report Inappropriate Project

class ProjectReport:
    VALID_REASONS = (
        "Inappropriate images",
        "Misleading information",
        "Offensive content",
        "Other",
    )

    def __init__(self, customer_id, project_id, reason, details=""):
        self.report_id = None
        self.customer_id = customer_id
        self.project_id = project_id
        self.reason = reason
        self.details = details
        self.status = "pending"
        self.submitted_at = None

    def submit(self):
        conn = get_db()

        try:
            self.submitted_at = now()

            cur = conn.execute(
                "INSERT INTO project_report "
                "(customer_id, project_id, reason, details, status, submitted_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (self.customer_id, self.project_id, self.reason, self.details, self.status, self.submitted_at),
            )

            conn.commit()
            self.report_id = cur.lastrowid
            return True

        except sqlite3.Error:
            conn.rollback()
            return False
