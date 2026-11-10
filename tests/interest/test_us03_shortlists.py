import pytest

from app.control.project_interest_controllers import (
    TrackProjectShortlistController, ViewShortlistCountsController,
)
from app.db import get_db
from app.entity.project import Project
from app.entity.project_shortlist import ProjectShortlist
from app.entity.user_account import UserAccount
from tests.conftest import login, make_user


@pytest.fixture
def customer(app):
    return make_user(UserAccount.CUSTOMER, "customer@test.local")


@pytest.fixture
def project(designer):
    project = Project(designer_id=designer.user_id, title="Modern HDB in Tampines",
                      description="A modern family home", location="Tampines",
                      completion_date="2027-03-20")
    assert project.create()
    return project


def test_customer_can_save_and_view_my_favourites(client, customer, project):
    login(client, customer.email)
    response = client.post(f"/projects/{project.project_id}/shortlist",
                           data={"action": "add"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Remove from shortlist" in response.data
    response = client.get("/projects/favourites")
    assert response.status_code == 200
    assert b"Modern HDB in Tampines" in response.data
    assert b"Remove favourite" in response.data


def test_home_links_to_my_favourites(client, customer):
    login(client, customer.email)
    page = client.get("/")
    assert b"My Favourites" in page.data
    assert b"/projects/favourites" in page.data


def test_duplicate_save_only_counts_once(customer, project):
    controller = TrackProjectShortlistController()
    assert controller.set_shortlisted(customer.user_id, project.project_id, "add")
    assert controller.result == "added"
    assert controller.set_shortlisted(customer.user_id, project.project_id, "add")
    assert controller.result == "already_saved"
    assert ProjectShortlist.counts_by_project([project.project_id]) == {project.project_id: 1}
    assert get_db().execute("SELECT COUNT(*) FROM project_shortlist_event").fetchone()[0] == 1


def test_designer_sees_exact_count_and_it_decreases_on_removal(client, customer, designer, project):
    login(client, customer.email)
    client.post(f"/projects/{project.project_id}/shortlist", data={"action": "add"})
    client.post("/logout")
    login(client, designer.email)
    page = client.get("/interest/")
    assert page.status_code == 200
    assert b"Modern HDB in Tampines" in page.data
    assert b"Your current project shortlist counts" in page.data
    metrics = ViewShortlistCountsController().get_counts(designer.user_id)
    assert metrics[0].shortlist_count == 1
    client.post("/logout")
    login(client, customer.email)
    client.post(f"/projects/{project.project_id}/shortlist",
                data={"action": "remove", "return_to": "favourites"})
    assert ViewShortlistCountsController().get_counts(designer.user_id)[0].shortlist_count == 0


def test_remove_using_my_favourites_button(client, customer, project):
    ProjectShortlist.add(customer.user_id, project.project_id)
    login(client, customer.email)
    response = client.post(f"/projects/{project.project_id}/shortlist",
                           data={"action": "remove", "return_to": "favourites"},
                           follow_redirects=True)
    assert response.status_code == 200
    assert b"You have not added any projects" in response.data
    assert not ProjectShortlist.is_saved(customer.user_id, project.project_id)


def test_two_distinct_customers_are_counted(customer, designer, project):
    second = make_user(UserAccount.CUSTOMER, "another@test.local")
    ProjectShortlist.add(customer.user_id, project.project_id)
    ProjectShortlist.add(second.user_id, project.project_id)
    assert ViewShortlistCountsController().get_counts(designer.user_id)[0].shortlist_count == 2


def test_designer_can_only_see_own_project_counts(client, customer, designer, other_designer, project):
    private = Project(designer_id=other_designer.user_id, title="Other designer project",
                      description="Secret", location="Bishan", completion_date="2027-04-25")
    assert private.create()
    ProjectShortlist.add(customer.user_id, private.project_id)
    login(client, designer.email)
    page = client.get("/interest/")
    assert b"Modern HDB in Tampines" in page.data
    assert b"Other designer project" not in page.data


def test_favourites_exclude_removed_project(client, customer, project):
    ProjectShortlist.add(customer.user_id, project.project_id)
    project.mark_removed()
    login(client, customer.email)
    assert b"Modern HDB in Tampines" not in client.get("/projects/favourites").data


def test_customer_cannot_see_designer_dashboard(client, customer):
    login(client, customer.email)
    assert client.get("/interest/").status_code == 403


def test_designer_cannot_access_customer_favourites(client, designer):
    login(client, designer.email)
    assert client.get("/projects/favourites").status_code == 403


def test_anonymous_cannot_access_favourites(client):
    response = client.get("/projects/favourites")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_removed_project_cannot_be_added(customer, project):
    project.mark_removed()
    controller = TrackProjectShortlistController()
    assert not controller.set_shortlisted(customer.user_id, project.project_id, "add")
    assert controller.errors == ["Project unavailable"]


def test_invalid_shortlist_action_is_rejected(customer, project):
    controller = TrackProjectShortlistController()
    assert not controller.set_shortlisted(customer.user_id, project.project_id, "nope")
    assert controller.errors == ["Invalid shortlist action"]


def test_suspended_customer_cannot_shortlist(customer, project):
    customer.set_status("suspended")
    assert not TrackProjectShortlistController().set_shortlisted(customer.user_id, project.project_id, "add")
