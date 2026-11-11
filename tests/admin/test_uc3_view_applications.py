import pytest

from app.control.admin_controllers import ViewApplicationController
from app.entity.interior_designer import InteriorDesigner
from app.entity.user_account import UserAccount
from tests.conftest import login, make_user

NOT_PENDING = "Application not found or no longer pending"


@pytest.fixture
def admin(app):
    return make_user(UserAccount.USER_ADMIN, "admin@test.local", name="Admin")


@pytest.fixture
def pending_designer(app):
    return make_user(UserAccount.INTERIOR_DESIGNER, "pending@test.local",
                     status="pending", name="Pending Studio")

@pytest.fixture
def pending_customer(app):
    return make_user(UserAccount.CUSTOMER, "customer@test.local",
                     status="pending", name="Pending Customer")


def test_find_pending_returns_only_pending_designers(pending_designer, designer, pending_customer):
    names = [d.name for d in InteriorDesigner.find_pending()]
    assert names == ["Pending Studio"]


def test_find_pending_returns_interior_designer_objects(pending_designer):
    results = InteriorDesigner.find_pending()
    assert len(results) == 1
    assert isinstance(results[0], InteriorDesigner)


def test_find_pending_is_empty_when_nobody_is_pending(designer):
    assert InteriorDesigner.find_pending() == []


def test_controller_lists_pending_applications(pending_designer, designer):
    applications = ViewApplicationController().get_pending_application()
    assert [d.name for d in applications] == ["Pending Studio"]


def test_get_application_returns_a_pending_designer(pending_designer):
    controller = ViewApplicationController()
    found = controller.get_application(pending_designer.user_id)
    assert found is not None
    assert found.name == "Pending Studio"
    assert controller.errors == []


def test_list_page_requires_login(client):
    response = client.get("/admin/")
    assert response.status_code == 302 and "/login" in response.headers["Location"]


def test_details_page_requires_login(client, pending_designer):
    response = client.get(f"/admin/{pending_designer.user_id}")
    assert response.status_code == 302 and "/login" in response.headers["Location"]


def test_designer_cannot_open_the_list_page(client, designer):
    login(client, designer.email)
    assert client.get("/admin/").status_code == 403


def test_customer_cannot_open_a_details_page(client, pending_designer):
    make_user(UserAccount.CUSTOMER, "c@test.local")
    login(client, "c@test.local")
    assert client.get(f"/admin/{pending_designer.user_id}").status_code == 403


def test_admin_sees_only_pending_applications(client, admin, pending_designer, designer):
    login(client, admin.email)
    response = client.get("/admin/")
    assert response.status_code == 200
    assert b"Pending Studio" in response.data
    assert b"Dana Designer" not in response.data


def test_list_shows_message_when_no_pending(client, admin):
    login(client, admin.email)
    response = client.get("/admin/")
    assert response.status_code == 200
    assert b"No pending applications" in response.data


def test_list_links_to_the_details_page(client, admin, pending_designer):
    login(client, admin.email)
    response = client.get("/admin/")
    assert f"/admin/{pending_designer.user_id}".encode() in response.data


def test_admin_can_open_a_pending_details_page(client, admin, pending_designer):
    login(client, admin.email)
    response = client.get(f"/admin/{pending_designer.user_id}")
    assert response.status_code == 200
    assert b"Pending Studio" in response.data
