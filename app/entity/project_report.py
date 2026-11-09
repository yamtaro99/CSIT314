import sqlite3

from app.db import get_db, now


# UC37 Report Inappropriate Project

class ProjectReport:
    
    # reasons that customers can choose when reporting a project
    VALID_REASONS = (
        "Inappropriate images",
        "Misleading information",
        "Offensive content",
        "Other",
    )

    # store the details of the report entered by customers
    def __init__(self, customer_id, project_id, reason, details=""):
        self.report_id = None
        self.customer_id = customer_id
        self.project_id = project_id
        self.reason = reason
        self.details = details
        self.status = "pending"
        self.submitted_at = None

    # save customers' report into the database
    def submit(self):
        conn = get_db()

        try:
            # record the date and time when the report is submitted
            self.submitted_at = now()

            cur = conn.execute(
                "INSERT INTO project_report "
                "(customer_id, project_id, reason, details, status, submitted_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (self.customer_id, self.project_id, self.reason, self.details, self.status, self.submitted_at),
            )

            # save the report and store its newly generated ID
            conn.commit()
            self.report_id = cur.lastrowid
            return True

        # undo the changes if there is a database error
        except sqlite3.Error:
            conn.rollback()
            return False