import pytest

from app.control.customer_project_controllers import ReportProjectController
from app.db import get_db
from app.entity.project import Project
from app.entity.project_report import ProjectReport
from app.entity.user_account import UserAccount
from tests.conftest import login, make_user


# UC37 Report Inappropriate Project

@pytest.fixture
def customer(app):
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

def count_reports():
    return get_db().execute(
        "SELECT COUNT(*) FROM project_report"
    ).fetchone()[0]


def test_project_report_saves_to_database(customer, project):
    report = ProjectReport(
        customer.user_id,
        project.project_id,
        "Misleading information",
        "Incorrect project details"
    )

    assert report.submit() is True
    assert report.report_id is not None

    row = get_db().execute(
        "SELECT * FROM project_report WHERE report_id = ?",
        (report.report_id,)
    ).fetchone()

    assert row["customer_id"] == customer.user_id
    assert row["project_id"] == project.project_id
    assert row["reason"] == "Misleading information"
    assert row["status"] == "pending"


def test_controller_accepts_valid_report(customer, project):
    controller = ReportProjectController()

    result = controller.report_project(
        customer.user_id,
        project.project_id,
        "Other",
        "Wrong photos"
    )

    assert result is True
    assert controller.errors == []
    assert count_reports() == 1

def test_controller_rejects_missing_reason(customer, project):
    controller = ReportProjectController()

    result = controller.report_project(
        customer.user_id,
        project.project_id,
        "",
        ""
    )

    assert result is False
    assert controller.errors == ["Please select a reason"]
    assert count_reports() == 0


def test_customer_can_open_report_form(client, customer, project):
    login(client, customer.email)

    response = client.get(
        f"/projects/{project.project_id}/report"
    )

    assert response.status_code == 200
    assert b"Report Project" in response.data
    assert b"Select a reason" in response.data

def test_customer_can_submit_report(client, customer, project):
    login(client, customer.email)

    response = client.post(
        f"/projects/{project.project_id}/report",
        data={
            "reason": "Other",
            "details": "Incorrect information"
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Report submitted successfully" in response.data
    assert count_reports() == 1

def test_cancel_does_not_save_report(client, customer, project):
    login(client, customer.email)

    response = client.post(
        f"/projects/{project.project_id}/report/cancel"
    )

    assert response.status_code == 302
    assert count_reports() == 0

def test_database_failure_displays_error(client, customer, project, monkeypatch):
    login(client, customer.email)

    monkeypatch.setattr(
        ProjectReport,
        "submit",
        lambda self: False
    )

    response = client.post(
        f"/projects/{project.project_id}/report",
        data={
            "reason": "Other",
            "details": "Test"
        }
    )

    assert response.status_code == 400
    assert b"Unable to submit report" in response.data
    assert count_reports() == 0
