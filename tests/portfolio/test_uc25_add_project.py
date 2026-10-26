from app.control.portfolio_controllers import AddProjectController
from app.entity.portfolio import Portfolio
from app.entity.user_account import UserAccount
from tests.conftest import login, make_user

VALID = dict(title="Tampines HDB Makeover", description="Full 4-room renovation",
             location="Tampines", completion_date="2026-03-15")


def test_add_valid_project_appears_in_portfolio(designer):
    controller = AddProjectController()
    assert controller.add_project(designer.user_id, **VALID) is True
    projects = Portfolio(designer.user_id).get_projects()
    assert [p.title for p in projects] == ["Tampines HDB Makeover"]
    assert projects[0].status == "active"


def test_missing_required_field_is_rejected(designer):
    controller = AddProjectController()
    assert controller.add_project(designer.user_id, **{**VALID, "location": "   "}) is False
    assert controller.errors == ["Please complete all required fields"]
    assert Portfolio(designer.user_id).get_projects() == []


def test_invalid_completion_date_is_rejected(designer):
    controller = AddProjectController()
    assert controller.add_project(designer.user_id, **{**VALID, "completion_date": "31/02/2026"}) is False
    assert "valid date" in controller.errors[0]


def test_title_longer_than_120_chars_is_rejected(designer):
    controller = AddProjectController()
    assert controller.add_project(designer.user_id, **{**VALID, "title": "x" * 121}) is False


def test_page_adds_project_and_shows_success(client, designer):
    login(client, designer.email)
    response = client.post("/portfolio/add", data=VALID, follow_redirects=True)
    assert b"Project added" in response.data
    assert b"Tampines HDB Makeover" in response.data


def test_customer_cannot_open_add_project_page(client, app):
    make_user(UserAccount.CUSTOMER, "c@test.local")
    login(client, "c@test.local")
    assert client.get("/portfolio/add").status_code == 403
