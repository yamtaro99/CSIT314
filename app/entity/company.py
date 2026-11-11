from app.db import get_db


class Company:
    def __init__(self, designer_id, registration_no, address="", phone="",
                 description="", company_id=None):
        self.company_id = company_id
        self.designer_id = designer_id
        self.registration_no = registration_no
        self.address = address
        self.phone = phone
        self.description = description

    @classmethod
    def _from_row(cls, row):
        return cls(
            company_id=row["company_id"], designer_id=row["designer_id"],
            registration_no=row["registration_no"], address=row["address"],
            phone=row["phone"], description=row["description"],
        )

    @classmethod
    def find_by_designer(cls, designer_id):
        row = get_db().execute(
            "SELECT * FROM company WHERE designer_id = ?", (designer_id,)
        ).fetchone()
        return cls._from_row(row) if row else None
