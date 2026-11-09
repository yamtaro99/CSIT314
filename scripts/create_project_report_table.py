import os
import sys

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
))


from app import create_app
from app.db import get_db


# UC37 Report Inappropriate Project

# connect to the application's database
app = create_app()

with app.app_context():
    conn = get_db()

    # create the report table if it does not already exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_report(
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES user_account(user_id),
            project_id INTEGER NOT NULL REFERENCES project(project_id),
            reason TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved')),
            submitted_at TEXT NOT NULL
        )
    """)

    # save the new table into the database
    conn.commit()

    print("Database:", app.config["DATABASE"])
    print("Project report table ready!")