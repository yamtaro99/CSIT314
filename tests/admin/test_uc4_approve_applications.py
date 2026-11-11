import pytest

from app.control.admin_controllers import ApproveApplicationController
from app.control.login_controller import LoginController
from app.entity.interior_designer import InteriorDesigner
from app.entity.user_account import UserAccount
from tests.conftest import PASSWORD, login, make_user

NOT_PENDING = "Application not found or no longer pending"


@pytest.fixture
def admin(app):
    return make_user(UserAccount.USER_ADMIN, "admin@test.local", name="Admin")


@pytest.fixture
def pending_designer(app):
    return make_user(UserAccount.INTERIOR_DESIGNER, "pending@test.local",
                     status="pending", name="Pending Studio")


def test_set_status_saves_to_the_database(pending_designer):
    designer = InteriorDesigner.find_by_id(pending_designer.user_id)
    assert designer.set_status("active") is True
    assert UserAccount.find_by_id(pending_designer.user_id).status == "active"


def test_find_by_id_ignores_other_roles(app):
    customer = make_user(UserAccount.CUSTOMER, "cust@test.local", status="pending")
    assert InteriorDesigner.find_by_id(customer.user_id) is None


def test_approve_pending_designer_succeeds(pending_designer):
    controller = ApproveApplicationController()
    assert controller.approve_application(pending_designer.user_id) is True
    assert controller.errors == []
    assert controller.designer.name == "Pending Studio"
    assert InteriorDesigner.find_by_id(pending_designer.user_id).status == "active"


def test_approving_twice_fails_the_second_time(pending_designer):
    ApproveApplicationController().approve_application(pending_designer.user_id)
    controller = ApproveApplicationController()
    assert controller.approve_application(pending_designer.user_id) is False
    assert controller.errors == [NOT_PENDING]


def test_approve_active_designer_is_refused(designer):
    controller = ApproveApplicationController()
    assert controller.approve_application(designer.user_id) is False
    assert controller.errors == [NOT_PENDING]
    assert InteriorDesigner.find_by_id(designer.user_id).status == "active"


def test_designer_can_log_in_only_after_approval(pending_designer):
    assert LoginController().login("pending@test.local", PASSWORD) is None
    ApproveApplicationController().approve_application(pending_designer.user_id)
    assert LoginController().login("pending@test.local", PASSWORD) is not None


def test_designer_cannot_approve(client, designer, pending_designer):
    login(client, designer.email)
    response = client.post(f"/admin/{pending_designer.user_id}/approve")
    assert response.status_code == 403
    assert InteriorDesigner.find_by_id(pending_designer.user_id).status == "pending"


def test_anonymous_visitor_cannot_approve(client, pending_designer):
    response = client.post(f"/admin/{pending_designer.user_id}/approve")
    assert response.status_code == 302 and "/login" in response.headers["Location"]
    assert InteriorDesigner.find_by_id(pending_designer.user_id).status == "pending"


def test_confirm_page_shows_the_applicant_and_changes_nothing(client, admin, pending_designer):
    login(client, admin.email)
    response = client.get(f"/admin/{pending_designer.user_id}/approve")
    assert response.status_code == 200
    assert b"Confirm" in response.data and b"Pending Studio" in response.data
    assert InteriorDesigner.find_by_id(pending_designer.user_id).status == "pending"


def test_post_approve_shows_success_and_updates_status(client, admin, pending_designer):
    login(client, admin.email)
    response = client.post(f"/admin/{pending_designer.user_id}/approve", follow_redirects=True)
    assert b"Application approved for Pending Studio" in response.data
    assert InteriorDesigner.find_by_id(pending_designer.user_id).status == "active"


def test_post_approve_for_active_designer_shows_error(client, admin, designer):
    login(client, admin.email)
    response = client.post(f"/admin/{designer.user_id}/approve", follow_redirects=True)
    assert NOT_PENDING.encode() in response.data
    assert InteriorDesigner.find_by_id(designer.user_id).status == "active"
