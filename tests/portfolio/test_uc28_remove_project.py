import pytest

from app.control.portfolio_controllers import AddProjectController, RemoveProjectController
from app.entity.portfolio import Portfolio
from app.entity.project import Project
from tests.conftest import login


@pytest.fixture
def project(designer):
    c = AddProjectController()
    c.add_project(designer.user_id, "Condo", "Minimalist condo", "Novena", "2024-08-20")
    return c.project


def test_removed_project_leaves_portfolio_but_row_is_kept(designer, project):
    assert RemoveProjectController().remove_project(project.project_id, designer.user_id) is True
    assert Portfolio(designer.user_id).get_projects() == []
    assert Project.find_by_id(project.project_id).status == "removed"


def test_cannot_remove_another_designers_project(other_designer, project):
    assert RemoveProjectController().remove_project(project.project_id, other_designer.user_id) is False
    assert Project.find_by_id(project.project_id).status == "active"


def test_removing_twice_fails(designer, project):
    controller = RemoveProjectController()
    controller.remove_project(project.project_id, designer.user_id)
    assert controller.remove_project(project.project_id, designer.user_id) is False


def test_get_shows_confirmation_and_does_not_remove(client, designer, project):
    login(client, designer.email)
    response = client.get(f"/portfolio/{project.project_id}/remove")
    assert b"Remove project?" in response.data
    assert Project.find_by_id(project.project_id).status == "active"
