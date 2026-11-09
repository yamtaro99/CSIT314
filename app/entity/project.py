from datetime import date

from app.db import get_db, now
from app.entity.category import Category
from app.entity.project_photo import ProjectPhoto
from app.entity.company import Company
from app.entity.user_account import UserAccount


class Project:
    EDITABLE_FIELDS = ("title", "description", "location", "completion_date")
    MAX_TITLE_LENGTH = 120

    def __init__(self, designer_id, title, description, location, completion_date,
                 project_id=None, status="active", created_at=None, updated_at=None):
        self.project_id = project_id
        self.designer_id = designer_id
        self.title = title
        self.description = description
        self.location = location
        self.completion_date = completion_date
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.errors = []

    def validate(self):
        errors = []
        for field in self.EDITABLE_FIELDS:
            value = getattr(self, field)
            value = value.strip() if isinstance(value, str) else value
            setattr(self, field, value)
            if not value:
                errors.append("Please complete all required fields")
                break
        if self.title and len(self.title) > self.MAX_TITLE_LENGTH:
            errors.append(f"Title must be {self.MAX_TITLE_LENGTH} characters or fewer")
        if self.completion_date:
            try:
                date.fromisoformat(str(self.completion_date))
            except ValueError:
                errors.append("Completion date must be a valid date (YYYY-MM-DD)")
        self.errors = errors
        return not errors

    def is_ongoing(self):
        return str(self.completion_date) > date.today().isoformat()

    def create(self):
        if not self.validate():
            return False
        self.created_at = self.updated_at = now()
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO project (designer_id, title, description, location, completion_date,"
            " status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (self.designer_id, self.title, self.description, self.location,
             str(self.completion_date), self.status, self.created_at, self.updated_at),
        )
        conn.commit()
        self.project_id = cur.lastrowid
        return True

    def update(self, details):
        original = {f: getattr(self, f) for f in self.EDITABLE_FIELDS}
        for field in self.EDITABLE_FIELDS:
            if field in details:
                setattr(self, field, details[field])
        if not self.validate():
            for field, value in original.items():
                setattr(self, field, value)
            return False
        self.updated_at = now()
        conn = get_db()
        conn.execute(
            "UPDATE project SET title = ?, description = ?, location = ?, completion_date = ?,"
            " updated_at = ? WHERE project_id = ?",
            (self.title, self.description, self.location, str(self.completion_date),
             self.updated_at, self.project_id),
        )
        conn.commit()
        return True

    def mark_removed(self):
        if self.status == "removed":
            return False
        self.status = "removed"
        self.updated_at = now()
        conn = get_db()
        conn.execute("UPDATE project SET status = 'removed', updated_at = ? WHERE project_id = ?",
                     (self.updated_at, self.project_id))
        conn.commit()
        return True

    def add_photo(self, photo):
        photo.project_id = self.project_id
        return photo.save()

    def set_categories(self, categories):
        if not categories:
            return False
        conn = get_db()
        conn.execute("DELETE FROM project_category WHERE project_id = ?", (self.project_id,))
        conn.executemany(
            "INSERT INTO project_category (project_id, category_id) VALUES (?, ?)",
            [(self.project_id, c.category_id) for c in categories],
        )
        conn.commit()
        return True

    def get_photos(self):
        return ProjectPhoto.find_by_project(self.project_id)

    def get_categories(self):
        rows = get_db().execute(
            "SELECT c.* FROM category c JOIN project_category pc ON pc.category_id = c.category_id"
            " WHERE pc.project_id = ? ORDER BY c.name",
            (self.project_id,),
        ).fetchall()
        return [Category._from_row(r) for r in rows]

    # UC31 - get the photos, categories and designer information for the selected project
    def get_details(self):
        return {
            "photos": self.get_photos(),
            "categories": self.get_categories(),
            "designer": UserAccount.find_by_id(self.designer_id),
            "company": Company.find_by_designer(self.designer_id),
        }

    @classmethod
    def _from_row(cls, row):
        return cls(
            project_id=row["project_id"], designer_id=row["designer_id"], title=row["title"],
            description=row["description"], location=row["location"],
            completion_date=row["completion_date"], status=row["status"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    @classmethod
    def find_by_id(cls, project_id):
        row = get_db().execute("SELECT * FROM project WHERE project_id = ?", (project_id,)).fetchone()
        return cls._from_row(row) if row else None

    @classmethod
    def find_active_by_designer(cls, designer_id):
        rows = get_db().execute(
            "SELECT * FROM project WHERE designer_id = ? AND status = 'active'"
            " ORDER BY completion_date DESC, project_id DESC",
            (designer_id,),
        ).fetchall()
        return [cls._from_row(r) for r in rows]

    # UC31 - find active projects that belong to active IDs
    @classmethod
    def find_available_projects(cls):
        rows = get_db().execute(
            "SELECT p.* FROM project p JOIN user_account u ON p.designer_id = u.user_id"
            " WHERE p.status = 'active' AND u.status = 'active'"
            " AND u.role = 'interior_designer'"
            " ORDER BY p.completion_date DESC, p.project_id DESC"
        ).fetchall()
        return [cls._from_row(r) for r in rows]