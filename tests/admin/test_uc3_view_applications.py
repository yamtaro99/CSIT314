import pytest

from app.control.admin_controllers import ViewApplicationController
from app.entity.interior_designer import InteriorDesigner
from app.entity.user_account import UserAccount
from tests.conftest import login, make_user

# The error message the control gives when an application can't be shown
NOT_PENDING = "Application not found or no longer pending"


@pytest.fixture
def admin(app):
    # Only user admin allowed to review applications
    return make_user(UserAccount.USER_ADMIN, "admin@test.local", name="Admin")


@pytest.fixture
def pending_designer(app):
    # An interior designer who has applied and is waiting for approval
    return make_user(UserAccount.INTERIOR_DESIGNER, "pending@test.local",
                     status="pending", name="Pending Studio")

@pytest.fixture
def pending_customer(app):
    # A pending account with the wrong role, which must never show up as an ID application
    return make_user(UserAccount.CUSTOMER, "customer@test.local",
                     status="pending", name="Pending Customer")

# ---------- Entity ----------

# find_pending() returns only pending interior designers, not active designers or pending customers
def test_find_pending_returns_only_pending_designers(pending_designer, designer, pending_customer):
    names = [d.name for d in InteriorDesigner.find_pending()]
    assert names == ["Pending Studio"]


# find_pending() builds InteriorDesigner objects, not plain rows or UserAccount objects
def test_find_pending_returns_interior_designer_objects(pending_designer):
    results = InteriorDesigner.find_pending()
    assert len(results) == 1
    assert isinstance(results[0], InteriorDesigner)


# find_pending() gives an empty list when no one is waiting
def test_find_pending_is_empty_when_nobody_is_pending(designer):
    assert InteriorDesigner.find_pending() == []


# ---------- Control ----------

# The controller's list contains the pending designer and leaves out the active one
def test_controller_lists_pending_applications(pending_designer, designer):
    applications = ViewApplicationController().get_pending_application()
    assert [d.name for d in applications] == ["Pending Studio"]


# get_application() returns the designer when they are still pending, with no errors
def test_get_application_returns_a_pending_designer(pending_designer):
    controller = ViewApplicationController()
    found = controller.get_application(pending_designer.user_id)
    assert found is not None
    assert found.name == "Pending Studio"
    assert controller.errors == []


# ---------- Boundary: access control ----------

# A visitor who isn't logged in is redirected from the list page to the login page
def test_list_page_requires_login(client):
    response = client.get("/admin/")
    assert response.status_code == 302 and "/login" in response.headers["Location"]


# A visitor who isn't logged in is redirected from a details page to the login page
def test_details_page_requires_login(client, pending_designer):
    response = client.get(f"/admin/{pending_designer.user_id}")
    assert response.status_code == 302 and "/login" in response.headers["Location"]


# A logged-in designer cannot access the admin list page
def test_designer_cannot_open_the_list_page(client, designer):
    login(client, designer.email)
    assert client.get("/admin/").status_code == 403


# A logged-in customer cannot access application's details page
def test_customer_cannot_open_a_details_page(client, pending_designer):
    make_user(UserAccount.CUSTOMER, "c@test.local")
    login(client, "c@test.local")
    assert client.get(f"/admin/{pending_designer.user_id}").status_code == 403


# ---------- Boundary: the pages ----------

# The admin's list shows the pending studio
def test_admin_sees_only_pending_applications(client, admin, pending_designer, designer):
    login(client, admin.email)
    response = client.get("/admin/")
    assert response.status_code == 200
    assert b"Pending Studio" in response.data
    assert b"Dana Designer" not in response.data


# If no pending applications, displays "No pending applications."
def test_list_shows_message_when_no_pending(client, admin):
    login(client, admin.email)
    response = client.get("/admin/")
    assert response.status_code == 200
    assert b"No pending applications" in response.data


# Each studio name on the list links to that applicant's details page
def test_list_links_to_the_details_page(client, admin, pending_designer):
    login(client, admin.email)
    response = client.get("/admin/")
    assert f"/admin/{pending_designer.user_id}".encode() in response.data


# The admin can open the details page of a pending applicant and see their name
def test_admin_can_open_a_pending_details_page(client, admin, pending_designer):
    login(client, admin.email)
    response = client.get(f"/admin/{pending_designer.user_id}")
    assert response.status_code == 200
    assert b"Pending Studio" in response.data
