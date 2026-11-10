from datetime import date, timedelta
from app.db import get_db, now


class ProjectView:
    @staticmethod
    def record(customer_id, project_id):
        conn = get_db()
        conn.execute(
            "INSERT INTO project_view (customer_id, project_id, viewed_at) VALUES (?, ?, ?)",
            (customer_id, project_id, now()),
        )
        conn.commit()

    @staticmethod
    def counts_by_project(project_ids):
        if not project_ids:
            return {}
        placeholders = ",".join("?" for _ in project_ids)
        rows = get_db().execute(
            f"SELECT project_id, COUNT(*) AS total FROM project_view "
            f"WHERE project_id IN ({placeholders}) GROUP BY project_id",
            tuple(project_ids),
        ).fetchall()
        return {row["project_id"]: row["total"] for row in rows}

    @staticmethod
    def weekly_counts(project_ids, start_date, end_date):
        if not project_ids:
            return {}
        placeholders = ",".join("?" for _ in project_ids)
        rows = get_db().execute(
            "SELECT substr(viewed_at, 1, 10) AS event_day, COUNT(*) AS total "
            "FROM project_view "
            f"WHERE project_id IN ({placeholders}) AND viewed_at >= ? AND viewed_at < ? "
            "GROUP BY substr(viewed_at, 1, 10)",
            (*project_ids, start_date.isoformat(), end_date.isoformat()),
        ).fetchall()
        counts = {}
        for row in rows:
            day = date.fromisoformat(row["event_day"])
            monday = day - timedelta(days=day.weekday())
            counts[monday] = counts.get(monday, 0) + row["total"]
        return counts
