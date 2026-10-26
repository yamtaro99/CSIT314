import pytest

from app.control.portfolio_controllers import AddProjectController, TagProjectController
from app.db import get_db
from app.entity.project import Project


@pytest.fixture
def project(designer):
    c = AddProjectController()
    c.add_project(designer.user_id, "Bungalow", "Tropical bungalow", "Sentosa", "2025-06-30")
    return c.project


def test_get_categories_returns_only_active(categories):
    get_db().execute("UPDATE category SET is_active = 0 WHERE name = 'Industrial'")
    names = [c.name for c in TagProjectController().get_categories()]
    assert names == ["Modern", "Scandinavian"]


def test_tag_project_saves_categories(designer, project, categories):
    ids = [str(categories[0].category_id), str(categories[1].category_id)]
    assert TagProjectController().tag_project(project.project_id, ids, designer.user_id) is True
    names = [c.name for c in Project.find_by_id(project.project_id).get_categories()]
    assert names == ["Modern", "Scandinavian"]


def test_retagging_replaces_old_categories(designer, project, categories):
    controller = TagProjectController()
    controller.tag_project(project.project_id, [categories[0].category_id], designer.user_id)
    controller.tag_project(project.project_id, [categories[2].category_id], designer.user_id)
    names = [c.name for c in Project.find_by_id(project.project_id).get_categories()]
    assert names == ["Industrial"]


def test_no_category_selected(designer, project, categories):
    controller = TagProjectController()
    assert controller.tag_project(project.project_id, [], designer.user_id) is False
    assert controller.errors == ["Select at least one category"]


def test_inactive_or_unknown_category_is_rejected(designer, project, categories):
    controller = TagProjectController()
    assert controller.tag_project(project.project_id, [9999], designer.user_id) is False


def test_cannot_tag_another_designers_project(other_designer, project, categories):
    controller = TagProjectController()
    assert controller.tag_project(project.project_id, [categories[0].category_id], other_designer.user_id) is False
