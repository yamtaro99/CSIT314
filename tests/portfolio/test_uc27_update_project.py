import pytest

from app.control.portfolio_controllers import AddProjectController, UpdateProjectController
from app.entity.project import Project
from tests.conftest import login


@pytest.fixture
def project(designer):
    c = AddProjectController()
    c.add_project(designer.user_id, "Old title", "Old description", "Jurong", "2025-01-10")
    return c.project


def test_update_saves_new_details(designer, project):
    controller = UpdateProjectController()
    ok = controller.update_project(project.project_id, {"title": "New title", "location": "Clementi"}, designer.user_id)
    assert ok is True
    saved = Project.find_by_id(project.project_id)
    assert (saved.title, saved.location, saved.description) == ("New title", "Clementi", "Old description")


def test_update_refreshes_last_updated_timestamp(designer, project):
    before = Project.find_by_id(project.project_id).updated_at
    UpdateProjectController().update_project(project.project_id, {"title": "Changed"}, designer.user_id)
    assert Project.find_by_id(project.project_id).updated_at >= before


def test_invalid_update_changes_nothing(designer, project):
    controller = UpdateProjectController()
    assert controller.update_project(project.project_id, {"title": ""}, designer.user_id) is False
    assert controller.errors == ["Please complete all required fields"]
    assert Project.find_by_id(project.project_id).title == "Old title"


def test_cannot_update_another_designers_project(other_designer, project):
    controller = UpdateProjectController()
    assert controller.update_project(project.project_id, {"title": "Hacked"}, other_designer.user_id) is False
    assert Project.find_by_id(project.project_id).title == "Old title"


def test_edit_page_is_404_for_other_designer(client, other_designer, project):
    login(client, other_designer.email)
    assert client.get(f"/portfolio/{project.project_id}/edit").status_code == 404
