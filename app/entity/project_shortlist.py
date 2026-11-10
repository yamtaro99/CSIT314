from app.db import get_db, now
from app.entity.project import Project


class ProjectShortlist:
    @staticmethod
    def is_saved(customer_id, project_id):
        return get_db().execute(
            "SELECT 1 FROM project_shortlist WHERE customer_id = ? AND project_id = ?",
            (customer_id, project_id),
        ).fetchone() is not None

    @staticmethod
    def add(customer_id, project_id):
        conn = get_db()
        at = now()
        try:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO project_shortlist (customer_id, project_id, created_at) "
                "VALUES (?, ?, ?)",
                (customer_id, project_id, at),
            )
            if cursor.rowcount == 1:
                conn.execute(
                    "INSERT INTO project_shortlist_event (customer_id, project_id, action, event_at) "
                    "VALUES (?, ?, 'add', ?)",
                    (customer_id, project_id, at),
                )
            conn.commit()
            return cursor.rowcount == 1
        except Exception:
            conn.rollback()
            raise

    @staticmethod
    def remove(customer_id, project_id):
        conn = get_db()
        try:
            cursor = conn.execute(
                "DELETE FROM project_shortlist WHERE customer_id = ? AND project_id = ?",
                (customer_id, project_id),
            )
            if cursor.rowcount == 1:
                conn.execute(
                    "INSERT INTO project_shortlist_event (customer_id, project_id, action, event_at) "
                    "VALUES (?, ?, 'remove', ?)",
                    (customer_id, project_id, now()),
                )
            conn.commit()
            return cursor.rowcount == 1
        except Exception:
            conn.rollback()
            raise

    @staticmethod
    def counts_by_project(project_ids):
        if not project_ids:
            return {}
        placeholders = ",".join("?" for _ in project_ids)
        rows = get_db().execute(
            f"SELECT project_id, COUNT(*) AS total FROM project_shortlist "
            f"WHERE project_id IN ({placeholders}) GROUP BY project_id",
            tuple(project_ids),
        ).fetchall()
        return {row["project_id"]: row["total"] for row in rows}

    @staticmethod
    def favourites_for_customer(customer_id):
        rows = get_db().execute(
            "SELECT p.* FROM project_shortlist AS s "
            "JOIN project AS p ON p.project_id = s.project_id "
            "JOIN user_account AS d ON d.user_id = p.designer_id "
            "WHERE s.customer_id = ? AND p.status = 'active' "
            "AND d.role = 'interior_designer' AND d.status = 'active' "
            "ORDER BY s.created_at DESC, p.project_id DESC",
            (customer_id,),
        ).fetchall()
        return [Project._from_row(row) for row in rows]
