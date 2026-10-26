from app.db import get_db
from app.entity.portfolio import Portfolio
from app.entity.user_account import UserAccount


class InteriorDesigner(UserAccount):
    def __init__(self, email, name, status="active", **kwargs):
        kwargs.pop("role", None)
        super().__init__(email=email, name=name, role=UserAccount.INTERIOR_DESIGNER,
                         status=status, **kwargs)

    def get_portfolio(self):
        return Portfolio(self.user_id)

    @classmethod
    def find_by_id(cls, user_id):
        row = get_db().execute(
            "SELECT * FROM user_account WHERE user_id = ? AND role = ?",
            (user_id, UserAccount.INTERIOR_DESIGNER),
        ).fetchone()
        return cls._from_row(row) if row else None
