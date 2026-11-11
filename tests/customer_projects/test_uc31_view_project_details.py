import pytest

from app.control.customer_project_controllers import ViewProjectDetailsController
from app.entity.project import Project
from app.entity.user_account import UserAccount
from tests.conftest import login, make_user


# UC31 View Project Details

@pytest.fixture
def customer (app):
    return make_user(
        UserAccount.CUSTOMER,
        "customer@test.local",
        name="Casey Customer"
    )

@pytest.fixture
def project(designer):
    p = Project(
        designer_id=designer.user_id,
        title="Woodlands Family Home",
        description="A cosy four-room renovation",
        location="Woodlands",
        completion_date="2027-03-09",
    )

    assert p.create() is True
    return p


def test_find_by_id_returns_project(project):
    found = Project.find_by_id(project.project_id)

    assert found is not None
    assert found.title == "Woodlands Family Home"
    assert found.location == "Woodlands"


def test_controller_returns_active_project(project):
    controller = ViewProjectDetailsController()
    found = controller.get_project_details(project.project_id)

    assert found is not None
    assert found.project_id == project.project_id
    assert controller.errors == []


def test_controller_rejects_unknown_project(app):
    controller = ViewProjectDetailsController()

    assert controller.get_project_details(999999) is None
    assert controller.errors == ["Project unavailable"]


def test_customer_can_browse_and_view_details(client, customer, project, categories):
    assert project.set_categories([categories[0]]) is True
    login(client, customer.email)

    listing = client.get("/projects/")
    assert listing.status_code == 200
    assert b"Woodlands Family Home" in listing.data

    detail = client.get(f"/projects/{project.project_id}")
    assert detail.status_code == 200
    assert b"Woodlands Family Home" in detail.data
    assert b"A cosy four-room renovation" in detail.data
    assert b"Modern" in detail.data
    assert b"Dana Designer" in detail.data
