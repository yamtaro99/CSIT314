from datetime import date, timedelta

import pytest

from app.control.consultation_controllers import SetAvailabilityController
from app.db import get_db
from app.entity.interior_designer import InteriorDesigner
from app.entity.user_account import UserAccount
from tests.conftest import login, make_user

TOMORROW = (date.today() + timedelta(days=1)).isoformat()
YESTERDAY = (date.today() - timedelta(days=1)).isoformat()
FIXED_DAY = "2030-06-15"  # far enough ahead that the future check always passes


# ---------- local helpers (DB reads/inserts for slot setup) ----------

def insert_slot(app, designer_id, date_str, start, end, is_booked=0):
    with app.app_context():
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO consultation_slot (designer_id, date, start_time, end_time, is_booked)"
            " VALUES (?, ?, ?, ?, ?)",
            (designer_id, date_str, start, end, is_booked),
        )
        conn.commit()
        return cur.lastrowid


def fetch_slots(app, designer_id):
    with app.app_context():
        rows = get_db().execute(
            "SELECT slot_id, date, start_time, end_time, is_booked FROM consultation_slot"
            " WHERE designer_id = ? ORDER BY date, start_time",
            (designer_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def post_add(client, date_str, start, duration=None):
    data = {"date": date_str, "start_time": start}
    if duration is not None:
        data["duration"] = duration
    return client.post("/consultation/availability/add", data=data, follow_redirects=True)


@pytest.fixture
def designer_client(client, designer):
    login(client, designer.email)
    return client


# ---------- Controller: SetAvailabilityController.set_availability ----------

class TestSetAvailabilityController:

    def _run(self, app, designer_id, date_str, start, duration=1):
        with app.app_context():
            d = InteriorDesigner.find_by_id(designer_id)
            controller = SetAvailabilityController()
            ok = controller.set_availability(d, date_str, start, duration)
            return ok, controller.errors

    def test_future_one_hour_slot_is_saved_as_open(self, app, designer):
        ok, errors = self._run(app, designer.user_id, FIXED_DAY, "10:00", 1)

        assert ok is True
        assert errors == []
        slots = fetch_slots(app, designer.user_id)
        assert len(slots) == 1
        assert (slots[0]["start_time"], slots[0]["end_time"]) == ("10:00", "11:00")
        assert slots[0]["is_booked"] == 0

    def test_two_hour_duration_calculates_end_time(self, app, designer):
        ok, _ = self._run(app, designer.user_id, FIXED_DAY, "10:00", 2)

        assert ok is True
        assert fetch_slots(app, designer.user_id)[0]["end_time"] == "12:00"

    def test_past_slot_is_rejected(self, app, designer):
        ok, errors = self._run(app, designer.user_id, YESTERDAY, "10:00", 1)

        assert ok is False
        assert "The slot start time must be in the future." in errors
        assert fetch_slots(app, designer.user_id) == []

    def test_overlapping_slot_is_rejected(self, app, designer):
        insert_slot(app, designer.user_id, FIXED_DAY, "10:00", "11:00")

        ok, errors = self._run(app, designer.user_id, FIXED_DAY, "10:30", 1)

        assert ok is False
        assert "This time slot overlaps with an existing slot." in errors
        assert len(fetch_slots(app, designer.user_id)) == 1

    def test_slot_starting_earlier_but_running_into_existing_is_rejected(self, app, designer):
        insert_slot(app, designer.user_id, FIXED_DAY, "10:00", "11:00")

        ok, errors = self._run(app, designer.user_id, FIXED_DAY, "09:30", 1)

        assert ok is False
        assert "This time slot overlaps with an existing slot." in errors

    def test_back_to_back_slots_are_allowed(self, app, designer):
        insert_slot(app, designer.user_id, FIXED_DAY, "10:00", "11:00")

        ok_after, _ = self._run(app, designer.user_id, FIXED_DAY, "11:00", 1)
        ok_before, _ = self._run(app, designer.user_id, FIXED_DAY, "09:00", 1)

        assert ok_after is True
        assert ok_before is True
        assert len(fetch_slots(app, designer.user_id)) == 3

    def test_same_time_on_different_date_is_allowed(self, app, designer):
        insert_slot(app, designer.user_id, FIXED_DAY, "10:00", "11:00")

        ok, _ = self._run(app, designer.user_id, "2030-06-16", "10:00", 1)

        assert ok is True

    def test_other_designers_slots_do_not_block_booking(self, app, designer, other_designer):
        insert_slot(app, other_designer.user_id, FIXED_DAY, "10:00", "11:00")

        ok, _ = self._run(app, designer.user_id, FIXED_DAY, "10:00", 1)

        assert ok is True

    @pytest.mark.parametrize("date_str, start", [
        ("not-a-date", "10:00"),
        ("2030-13-45", "10:00"),
        ("2030-06-15", "25:99"),
        ("2030-06-15", "ten"),
    ])
    def test_invalid_date_or_time_format_is_rejected(self, app, designer, date_str, start):
        ok, errors = self._run(app, designer.user_id, date_str, start, 1)

        assert ok is False
        assert errors == ["Invalid date or time format provided."]
        assert fetch_slots(app, designer.user_id) == []


# ---------- Route: POST /consultation/availability/add ----------

class TestAddSlotRoute:

    def test_designer_adds_slot_and_sees_success_message(self, designer_client, app, designer):
        response = post_add(designer_client, FIXED_DAY, "10:00", "1")

        assert response.status_code == 200
        assert b"Consultation availability slot successfully added." in response.data
        assert len(fetch_slots(app, designer.user_id)) == 1

    def test_default_duration_is_one_hour_when_not_sent(self, designer_client, app, designer):
        post_add(designer_client, FIXED_DAY, "14:00")

        assert fetch_slots(app, designer.user_id)[0]["end_time"] == "15:00"

    def test_overlap_shows_error_and_does_not_save(self, designer_client, app, designer):
        insert_slot(app, designer.user_id, FIXED_DAY, "10:00", "11:00")

        response = post_add(designer_client, FIXED_DAY, "10:30", "1")

        assert b"This time slot overlaps with an existing slot." in response.data
        assert len(fetch_slots(app, designer.user_id)) == 1

    def test_past_slot_shows_error_and_does_not_save(self, designer_client, app, designer):
        response = post_add(designer_client, YESTERDAY, "10:00", "1")

        assert b"The slot start time must be in the future." in response.data
        assert fetch_slots(app, designer.user_id) == []

    def test_multiple_slots_can_be_added_in_a_row(self, designer_client, app, designer):
        post_add(designer_client, FIXED_DAY, "09:00", "1")
        post_add(designer_client, FIXED_DAY, "10:00", "2")
        post_add(designer_client, FIXED_DAY, "13:00", "1")

        slots = fetch_slots(app, designer.user_id)
        assert [(s["start_time"], s["end_time"]) for s in slots] == [
            ("09:00", "10:00"), ("10:00", "12:00"), ("13:00", "14:00"),
        ]

    def test_calendar_shows_new_slot_as_open(self, designer_client, designer):
        post_add(designer_client, FIXED_DAY, "10:00", "1")

        response = designer_client.get("/consultation/availability")

        assert b"Open" in response.data
        assert b"No availability slots" not in response.data


# ---------- Route: POST /consultation/availability/<slot_id>/delete ----------

class TestDeleteSlotRoute:

    def test_open_slot_is_removed_and_calendar_refreshed(self, designer_client, app, designer):
        slot_id = insert_slot(app, designer.user_id, FIXED_DAY, "10:00", "11:00")

        response = designer_client.post(
            f"/consultation/availability/{slot_id}/delete", follow_redirects=True
        )

        assert b"Open consultation slot removed." in response.data
        assert fetch_slots(app, designer.user_id) == []

    def test_booked_slot_is_refused_and_kept(self, designer_client, app, designer):
        slot_id = insert_slot(app, designer.user_id, FIXED_DAY, "10:00", "11:00", is_booked=1)

        response = designer_client.post(
            f"/consultation/availability/{slot_id}/delete", follow_redirects=True
        )

        assert b"This slot could not be removed" in response.data
        slots = fetch_slots(app, designer.user_id)
        assert len(slots) == 1 and slots[0]["is_booked"] == 1

    def test_designer_cannot_delete_another_designers_slot(self, designer_client, app, other_designer):
        slot_id = insert_slot(app, other_designer.user_id, FIXED_DAY, "10:00", "11:00")

        response = designer_client.post(
            f"/consultation/availability/{slot_id}/delete", follow_redirects=True
        )

        assert b"This slot could not be removed" in response.data
        assert len(fetch_slots(app, other_designer.user_id)) == 1

    def test_deleting_missing_slot_shows_error(self, designer_client):
        response = designer_client.post(
            "/consultation/availability/9999/delete", follow_redirects=True
        )

        assert b"This slot could not be removed" in response.data

    def test_deleted_slot_frees_its_time_for_a_new_booking(self, designer_client, app, designer):
        slot_id = insert_slot(app, designer.user_id, FIXED_DAY, "10:00", "11:00")
        designer_client.post(f"/consultation/availability/{slot_id}/delete")

        response = post_add(designer_client, FIXED_DAY, "10:00", "1")

        assert b"Consultation availability slot successfully added." in response.data
        assert len(fetch_slots(app, designer.user_id)) == 1


# ---------- Access control ----------

class TestAccessControl:

    def test_anonymous_user_is_redirected_to_login(self, client):
        response = client.get("/consultation/availability")

        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_customer_cannot_view_calendar(self, client):
        make_user(UserAccount.CUSTOMER, "c@test.local")
        login(client, "c@test.local")

        assert client.get("/consultation/availability").status_code == 403

    def test_customer_cannot_add_slot(self, client, app):
        customer = make_user(UserAccount.CUSTOMER, "c@test.local")
        login(client, "c@test.local")

        client.post("/consultation/availability/add",
                    data={"date": FIXED_DAY, "start_time": "10:00", "duration": "1"})

        assert fetch_slots(app, customer.user_id) == []

    def test_customer_cannot_delete_slot(self, client, app, designer):
        make_user(UserAccount.CUSTOMER, "c@test.local")
        slot_id = insert_slot(app, designer.user_id, FIXED_DAY, "10:00", "11:00")
        login(client, "c@test.local")

        assert client.post(f"/consultation/availability/{slot_id}/delete").status_code == 403
        assert len(fetch_slots(app, designer.user_id)) == 1