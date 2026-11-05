from app.db import get_db

class ConsultationSlot:
    def __init__(self, slotId, date, startTime, endTime, isBooked=False):
        self.slotId = slotId
        self.date = date
        self.startTime = startTime
        self.endTime = endTime
        self.isBooked = bool(isBooked)

    def create(self, designer_id):
        """Persists a new consultation slot associated with an interior designer."""
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO consultation_slot (designer_id, date, start_time, end_time, is_booked) "
            "VALUES (?, ?, ?, ?, ?)",
            (designer_id, str(self.date), str(self.startTime), str(self.endTime), int(self.isBooked))
        )
        conn.commit()
        self.slotId = cur.lastrowid
        return True

    def reserve(self):
        """Marks the slot as booked."""
        conn = get_db()
        conn.execute(
            "UPDATE consultation_slot SET is_booked = 1 WHERE slot_id = ?",
            (self.slotId,)
        )
        conn.commit()
        self.isBooked = True
        return True

    def release(self):
        """Marks the slot as unbooked/open."""
        conn = get_db()
        conn.execute(
            "UPDATE consultation_slot SET is_booked = 0 WHERE slot_id = ?",
            (self.slotId,)
        )
        conn.commit()
        self.isBooked = False
        return True

    @classmethod
    def _from_row(cls, row):
        return cls(
            slotId=row["slot_id"],
            date=row["date"],
            startTime=row["start_time"],
            endTime=row["end_time"],
            isBooked=row["is_booked"]
        )

    @classmethod
    def get_slots_by_designer(cls, designer_id):
        """Fetches all consultation slots created by a specific interior designer."""
        rows = get_db().execute(
            "SELECT * FROM consultation_slot WHERE designer_id = ? ORDER BY date ASC, start_time ASC",
            (designer_id,)
        ).fetchall()
        return [cls._from_row(r) for r in rows]