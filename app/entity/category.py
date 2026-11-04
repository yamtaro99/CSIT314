from app.db import get_db, now


class Category:
    def __init__(self, name, is_active=True, category_id=None, created_at=None):
        self.category_id = category_id
        self.name = name
        self.is_active = bool(is_active)
        self.created_at = created_at

    def create(self):
        if not (self.name or "").strip():
            return False
        self.created_at = now()
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO category (name, is_active, created_at) VALUES (?, ?, ?)",
            (self.name.strip(), int(self.is_active), self.created_at),
        )
        conn.commit()
        self.category_id = cur.lastrowid
        return True

    @classmethod
    def _from_row(cls, row):
        return cls(category_id=row["category_id"], name=row["name"],
                   is_active=row["is_active"], created_at=row["created_at"])

    @classmethod
    def get_active_categories(cls):
        rows = get_db().execute(
            "SELECT * FROM category WHERE is_active = 1 ORDER BY name"
        ).fetchall()
        return [cls._from_row(r) for r in rows]

    @classmethod
    def find_active_by_ids(cls, category_ids):
        ids = list(category_ids)
        if not ids:
            return []
        marks = ",".join("?" * len(ids))
        rows = get_db().execute(
            f"SELECT * FROM category WHERE is_active = 1 AND category_id IN ({marks})", ids
        ).fetchall()
        return [cls._from_row(r) for r in rows]
