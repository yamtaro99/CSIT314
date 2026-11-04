from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db, now


class UserAccount:
    USER_ADMIN = "user_admin"
    INTERIOR_DESIGNER = "interior_designer"
    CUSTOMER = "customer"
    PLATFORM_MANAGER = "platform_manager"
    ROLES = (USER_ADMIN, INTERIOR_DESIGNER, CUSTOMER, PLATFORM_MANAGER)

    def __init__(self, email, name, role, status="active",
                 user_id=None, password_hash=None, created_at=None):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.role = role
        self.status = status
        self.password_hash = password_hash
        self.created_at = created_at

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def is_active(self):
        return self.status == "active"

    def set_status(self, status):
        conn = get_db()
        conn.execute("UPDATE user_account SET status = ? WHERE user_id = ?",
                     (status, self.user_id))
        conn.commit()
        self.status = status
        return True

    def create(self):
        if self.role not in self.ROLES or not self.password_hash:
            return False
        self.created_at = now()
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO user_account (email, password_hash, name, role, status, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (self.email.strip().lower(), self.password_hash, self.name,
             self.role, self.status, self.created_at),
        )
        conn.commit()
        self.user_id = cur.lastrowid
        return True

    @classmethod
    def _from_row(cls, row):
        return cls(
            user_id=row["user_id"], email=row["email"], name=row["name"], role=row["role"],
            status=row["status"], password_hash=row["password_hash"], created_at=row["created_at"],
        )

    @classmethod
    def find_by_id(cls, user_id):
        row = get_db().execute("SELECT * FROM user_account WHERE user_id = ?", (user_id,)).fetchone()
        return cls._from_row(row) if row else None

    @classmethod
    def find_by_email(cls, email):
        row = get_db().execute(
            "SELECT * FROM user_account WHERE email = ?", ((email or "").strip().lower(),)
        ).fetchone()
        return cls._from_row(row) if row else None
