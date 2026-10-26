from app.control.login_controller import LoginController
from app.entity.user_account import UserAccount
from tests.conftest import PASSWORD, login, make_user


def test_login_succeeds_with_correct_password(app):
    make_user(UserAccount.CUSTOMER, "c@test.local")
    account = LoginController().login("C@Test.local ", PASSWORD)
    assert account is not None and account.role == UserAccount.CUSTOMER


def test_login_fails_with_wrong_password(app):
    make_user(UserAccount.CUSTOMER, "c@test.local")
    controller = LoginController()
    assert controller.login("c@test.local", "wrong") is None
    assert controller.error == "Incorrect email or password"


def test_login_fails_for_unknown_email(app):
    assert LoginController().login("nobody@test.local", PASSWORD) is None


def test_pending_designer_cannot_log_in(app):
    make_user(UserAccount.INTERIOR_DESIGNER, "p@test.local", status="pending")
    controller = LoginController()
    assert controller.login("p@test.local", PASSWORD) is None
    assert "approval" in controller.error


def test_suspended_user_cannot_log_in(app):
    make_user(UserAccount.CUSTOMER, "s@test.local", status="suspended")
    assert LoginController().login("s@test.local", PASSWORD) is None


def test_pages_require_login(client):
    response = client.get("/portfolio/")
    assert response.status_code == 302 and "/login" in response.headers["Location"]


def test_login_page_redirects_home(client, app):
    make_user(UserAccount.CUSTOMER, "c@test.local")
    response = login(client, "c@test.local")
    assert response.status_code == 302 and response.headers["Location"] == "/"


def test_login_ignores_offsite_next_url(client, app):
    make_user(UserAccount.CUSTOMER, "c@test.local")
    response = client.post("/login?next=//evil.example", data={"email": "c@test.local", "password": PASSWORD})
    assert response.headers["Location"] == "/"
