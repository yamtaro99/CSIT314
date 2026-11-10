import os
import random
import sys
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.db import get_db


def ensure_interest_tables(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS project_shortlist (
        customer_id INTEGER NOT NULL REFERENCES user_account(user_id),
        project_id INTEGER NOT NULL REFERENCES project(project_id),
        created_at TEXT NOT NULL,
        PRIMARY KEY (customer_id, project_id)
    );
    CREATE INDEX IF NOT EXISTS idx_shortlist_project ON project_shortlist(project_id);
    CREATE TABLE IF NOT EXISTS project_view (
        view_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL REFERENCES user_account(user_id),
        project_id INTEGER NOT NULL REFERENCES project(project_id),
        viewed_at TEXT NOT NULL,
        demo_event_key TEXT UNIQUE
    );
    CREATE INDEX IF NOT EXISTS idx_project_view_project ON project_view(project_id);
    CREATE TABLE IF NOT EXISTS project_shortlist_event (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL REFERENCES user_account(user_id),
        project_id INTEGER NOT NULL REFERENCES project(project_id),
        action TEXT NOT NULL CHECK(action IN ('add', 'remove')),
        event_at TEXT NOT NULL,
        demo_event_key TEXT UNIQUE
    );
    CREATE INDEX IF NOT EXISTS idx_shortlist_event_project_time
        ON project_shortlist_event(project_id, event_at);
    """)


def backfill_existing_shortlists(conn):
    cursor = conn.execute("""
    INSERT OR IGNORE INTO project_shortlist_event
        (customer_id, project_id, action, event_at, demo_event_key)
    SELECT s.customer_id, s.project_id, 'add', s.created_at,
           'legacy-favourite-' || s.customer_id || '-' || s.project_id || '-' || s.created_at
    FROM project_shortlist AS s
    WHERE NOT EXISTS (
        SELECT 1 FROM project_shortlist_event AS e
        WHERE e.customer_id = s.customer_id AND e.project_id = s.project_id
          AND e.action = 'add' AND e.event_at = s.created_at
    )
    """)
    return cursor.rowcount


def seed_demo_interest(conn, today=None):

    ensure_interest_tables(conn)
    migrated = backfill_existing_shortlists(conn)
    now = datetime.now()
    today = today or now.date()
    monday = today - timedelta(days=today.weekday())
    first_monday = monday - timedelta(weeks=7)
    customer_ids = [row[0] for row in conn.execute(
        "SELECT user_id FROM user_account WHERE role = 'customer' AND status = 'active' ORDER BY user_id"
    )]
    project_ids = [row[0] for row in conn.execute(
        "SELECT p.project_id FROM project AS p JOIN user_account AS u ON u.user_id = p.designer_id "
        "WHERE p.status = 'active' AND u.role = 'interior_designer' AND u.status = 'active' "
        "ORDER BY p.project_id"
    )]
    if not customer_ids or not project_ids:
        conn.commit()
        return {"projects": len(project_ids), "demo_views": 0,
                "shortlist_events_added": 0, "favourites_added": 0,
                "historical_favourites_migrated": migrated}

    views_added = events_added = favourites_added = 0
    # Not all weeks rise uniformly: realistic fluctuations with an overall pattern.
    view_pattern = [6, 8, 12, 9, 15, 13, 19, 14]
    shortlist_pattern = [1, 1, 2, 1, 3, 2, 4, 3]
    for project_id in project_ids:
        rng = random.Random(31403 + project_id)
        # Stable distinct customers per project, so a single favourite is not counted twice.
        candidates = rng.sample(customer_ids, min(30, len(customer_ids)))
        next_candidate = 0
        for week_idx in range(8):
            week_monday = first_monday + timedelta(weeks=week_idx)
            # A stable timestamp within the relevant calendar week.
            def timestamp_for(event_index):
                max_day = today.weekday() if week_idx == 7 else 6
                event_day = rng.randint(0, max_day)
                event_time = datetime.combine(week_monday + timedelta(days=event_day),
                                              datetime.min.time()) + timedelta(
                    hours=rng.randint(8, 20), minutes=rng.randint(0, 59))
                if event_time > now:
                    event_time = now - timedelta(minutes=1)
                return event_time.isoformat(timespec="seconds")

            weekly_views = max(1, view_pattern[week_idx] + rng.randint(-2, 4))
            for event_idx in range(weekly_views):
                customer_id = rng.choice(customer_ids)
                event_key = f"us07-v2-view-{first_monday}-{project_id}-{week_idx}-{event_idx}"
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO project_view "
                    "(customer_id, project_id, viewed_at, demo_event_key) VALUES (?, ?, ?, ?)",
                    (customer_id, project_id, timestamp_for(event_idx), event_key),
                )
                views_added += cursor.rowcount

            weekly_saves = max(0, shortlist_pattern[week_idx] + rng.randint(-1, 1))
            for event_idx in range(weekly_saves):
                if next_candidate >= len(candidates):
                    break
                customer_id = candidates[next_candidate]
                next_candidate += 1
                # Always advance the seeded RNG identically on reruns.
                timestamp = timestamp_for(event_idx)
                # Do not invent a second add while this customer already has
                # an active favourite (e.g., left over from the older patch).
                already_saved = conn.execute(
                    "SELECT 1 FROM project_shortlist WHERE customer_id = ? AND project_id = ?",
                    (customer_id, project_id),
                ).fetchone()
                if already_saved:
                    continue
                event_key = f"us07-v2-save-{first_monday}-{project_id}-{week_idx}-{event_idx}"
                cursor = conn.execute(
                    "INSERT OR IGNORE INTO project_shortlist_event "
                    "(customer_id, project_id, action, event_at, demo_event_key) "
                    "VALUES (?, ?, 'add', ?, ?)",
                    (customer_id, project_id, timestamp, event_key),
                )
                if cursor.rowcount == 1:
                    events_added += 1
                    favorite_cursor = conn.execute(
                        "INSERT OR IGNORE INTO project_shortlist "
                        "(customer_id, project_id, created_at) VALUES (?, ?, ?)",
                        (customer_id, project_id, timestamp),
                    )
                    favourites_added += favorite_cursor.rowcount
    conn.commit()
    return {"projects": len(project_ids), "demo_views": views_added,
            "shortlist_events_added": events_added, "favourites_added": favourites_added,
            "historical_favourites_migrated": migrated}


def main():
    app = create_app()
    with app.app_context():
        conn = get_db()
        result = seed_demo_interest(conn)
        print("Database:", app.config["DATABASE"])
        print("Synthetic weekly interest activity:", result)


if __name__ == "__main__":
    main()
