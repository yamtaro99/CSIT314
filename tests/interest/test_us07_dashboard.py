from datetime import date, timedelta

import pytest

from app.control.project_interest_controllers import ViewWeeklyInterestTrendsController
from app.db import get_db
from app.entity.project import Project
from app.entity.project_shortlist import ProjectShortlist
from app.entity.project_view import ProjectView
from app.entity.user_account import UserAccount
from scripts.seed_project_interest import seed_demo_interest
from tests.conftest import login, make_user


@pytest.fixture
def project(designer):
    p = Project(designer_id=designer.user_id, title="Quiet Kitchen in Bishan",
                description="Compact kitchen renovation", location="Bishan",
                completion_date="2027-03-20")
    assert p.create()
    return p


def _write_view(customer_id, project_id, when):
    get_db().execute(
        "INSERT INTO project_view(customer_id,project_id,viewed_at) VALUES (?, ?, ?)",
        (customer_id, project_id, when),
    )
    get_db().commit()


def _write_add(customer_id, project_id, when):
    get_db().execute(
        "INSERT INTO project_shortlist_event(customer_id,project_id,action,event_at) "
        "VALUES (?, ?, 'add', ?)",
        (customer_id, project_id, when),
    )
    get_db().commit()


def test_customer_detail_visit_records_a_view(client, project):
    customer = make_user(UserAccount.CUSTOMER, "view@test.local")
    login(client, customer.email)
    assert client.get(f"/projects/{project.project_id}").status_code == 200
    assert ProjectView.counts_by_project([project.project_id])[project.project_id] == 1


def test_weekly_graph_groups_views_and_adds_by_calendar_week(designer, project):
    customer = make_user(UserAccount.CUSTOMER, "view@test.local")
    # 10 Nov 2026 is Tuesday; week starts Monday 9 Nov.
    _write_view(customer.user_id, project.project_id, "2026-11-01T12:00:00")  # last Sunday
    _write_view(customer.user_id, project.project_id, "2026-11-02T12:00:00")  # Monday
    _write_view(customer.user_id, project.project_id, "2026-11-09T10:00:00")  # current Monday
    _write_add(customer.user_id, project.project_id, "2026-11-02T12:00:00")
    _write_add(customer.user_id, project.project_id, "2026-11-09T12:00:00")
    trend = ViewWeeklyInterestTrendsController().get_trends(
        designer.user_id, today=date(2026, 11, 10))
    assert len(trend.weeks) == 8
    assert trend.weeks[-3].week_start == "2026-10-26"
    assert trend.weeks[-3].views == 1
    assert trend.weeks[-2].week_start == "2026-11-02"
    assert trend.weeks[-2].views == 1
    assert trend.weeks[-2].shortlist_adds == 1
    assert trend.weeks[-1].views == 1
    assert trend.weeks[-1].shortlist_adds == 1


def test_weekly_add_remains_after_customer_removes_favourite(designer, project):
    customer = make_user(UserAccount.CUSTOMER, "short@test.local")
    assert ProjectShortlist.add(customer.user_id, project.project_id)
    assert ProjectShortlist.remove(customer.user_id, project.project_id)
    assert ProjectShortlist.counts_by_project([project.project_id]) == {}
    trend = ViewWeeklyInterestTrendsController().get_trends(designer.user_id)
    assert trend.weeks[-1].shortlist_adds == 1


def test_weekly_resave_records_second_add(designer, project):
    customer = make_user(UserAccount.CUSTOMER, "short@test.local")
    assert ProjectShortlist.add(customer.user_id, project.project_id)
    assert ProjectShortlist.remove(customer.user_id, project.project_id)
    assert ProjectShortlist.add(customer.user_id, project.project_id)
    assert ViewWeeklyInterestTrendsController().get_trends(designer.user_id).weeks[-1].shortlist_adds == 2
    assert ProjectShortlist.counts_by_project([project.project_id])[project.project_id] == 1


def test_chart_has_eight_points_and_nonzero_values(designer, project):
    customer = make_user(UserAccount.CUSTOMER, "view@test.local")
    ProjectView.record(customer.user_id, project.project_id)
    trend = ViewWeeklyInterestTrendsController().get_trends(designer.user_id)
    assert len(trend.views_chart.points) == 8
    assert len(trend.views_chart.polyline.split()) == 8
    assert trend.views_chart.total == 1


def test_designer_dashboard_renders_two_svg_graphs(client, designer, project):
    login(client, designer.email)
    response = client.get("/interest/")
    assert response.status_code == 200
    assert b"Weekly Views" in response.data
    assert b"Weekly New Shortlists" in response.data
    assert response.data.count(b"<svg") == 2
    assert b"Your current project shortlist counts" in response.data


def test_dashboard_can_select_owned_project(client, designer, project):
    login(client, designer.email)
    response = client.get(f"/interest/?project_id={project.project_id}")
    assert response.status_code == 200
    assert b"Quiet Kitchen in Bishan" in response.data


def test_reject_other_designers_project(client, designer, other_designer, project):
    private = Project(designer_id=other_designer.user_id, title="Other private project",
                      description="Secret", location="Yishun", completion_date="2027-03-20")
    assert private.create()
    login(client, designer.email)
    assert client.get(f"/interest/?project_id={private.project_id}").status_code == 404


def test_reject_invalid_project_id(client, designer):
    login(client, designer.email)
    assert client.get("/interest/?project_id=abc").status_code == 400


def test_non_designer_cannot_open_graph(client):
    customer = make_user(UserAccount.CUSTOMER, "customer@test.local")
    login(client, customer.email)
    assert client.get("/interest/").status_code == 403


def test_anonymous_redirects_to_login(client):
    assert client.get("/interest/").status_code == 302


def test_empty_projects_shows_zero_series(client, designer):
    login(client, designer.email)
    response = client.get("/interest/")
    assert response.status_code == 200
    assert b"No active projects to analyse yet" in response.data
    assert response.data.count(b"<svg") == 2


def test_demo_seed_is_repeatable_and_does_not_restore_removed_favourite(app, designer, project):
    customer = make_user(UserAccount.CUSTOMER, "customer@test.local")
    conn = get_db()
    first = seed_demo_interest(conn, today=date(2026, 11, 10))
    assert first["demo_views"] > 0
    assert first["shortlist_events_added"] > 0
    rows = conn.execute("SELECT customer_id, project_id FROM project_shortlist LIMIT 1").fetchone()
    assert rows is not None
    ProjectShortlist.remove(rows["customer_id"], rows["project_id"])
    second = seed_demo_interest(conn, today=date(2026, 11, 10))
    assert second["demo_views"] == 0
    assert second["shortlist_events_added"] == 0
    assert second["favourites_added"] == 0
    assert not ProjectShortlist.is_saved(rows["customer_id"], rows["project_id"])


def test_migration_backfills_older_favourites_exactly_once(app, designer, project):
    customer = make_user(UserAccount.CUSTOMER, "customer@test.local")
    conn = get_db()
    conn.execute("INSERT INTO project_shortlist(customer_id, project_id, created_at) "
                 "VALUES (?, ?, ?)", (customer.user_id, project.project_id, "2026-10-12T12:00:00"))
    conn.commit()
    from scripts.seed_project_interest import backfill_existing_shortlists
    assert backfill_existing_shortlists(conn) == 1
    assert backfill_existing_shortlists(conn) == 0
    conn.commit()
    assert conn.execute("SELECT COUNT(*) FROM project_shortlist_event").fetchone()[0] == 1
