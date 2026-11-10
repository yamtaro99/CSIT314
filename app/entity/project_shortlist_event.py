from datetime import date, timedelta
from app.db import get_db


class ProjectShortlistEvent:
    @staticmethod
    def weekly_add_counts(project_ids, start_date, end_date):
        if not project_ids:
            return {}
        placeholders = ",".join("?" for _ in project_ids)
        rows = get_db().execute(
            "SELECT substr(event_at, 1, 10) AS event_day, COUNT(*) AS total "
            "FROM project_shortlist_event "
            f"WHERE project_id IN ({placeholders}) AND action = 'add' "
            "AND event_at >= ? AND event_at < ? "
            "GROUP BY substr(event_at, 1, 10)",
            (*project_ids, start_date.isoformat(), end_date.isoformat()),
        ).fetchall()
        counts = {}
        for row in rows:
            day = date.fromisoformat(row["event_day"])
            monday = day - timedelta(days=day.weekday())
            counts[monday] = counts.get(monday, 0) + row["total"]
        return counts
