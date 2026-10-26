import os

import pytest

from app.control.portfolio_controllers import AddProjectController, UploadPhotoController
from app.entity.project import Project
from app.entity.project_photo import ProjectPhoto
from tests.conftest import JPG_BYTES, PNG_BYTES, upload


@pytest.fixture
def project(designer):
    c = AddProjectController()
    c.add_project(designer.user_id, "Loft", "Industrial loft", "Bukit Timah", "2025-11-01")
    return c.project


def test_valid_photos_are_saved_and_linked(app, designer, project):
    controller = UploadPhotoController()
    files = [upload("a.png", PNG_BYTES), upload("b.JPG", JPG_BYTES)]
    assert controller.upload_photos(project.project_id, files, designer.user_id) is True
    photos = Project.find_by_id(project.project_id).get_photos()
    assert len(photos) == 2
    for photo in photos:
        stored = os.path.join(app.config["UPLOAD_FOLDER"], photo.file_url.rsplit("/", 1)[-1])
        assert os.path.exists(stored)


def test_invalid_file_is_rejected_but_valid_ones_are_kept(designer, project):
    controller = UploadPhotoController()
    files = [upload("ok.png", PNG_BYTES), upload("notes.txt", b"hello")]
    assert controller.upload_photos(project.project_id, files, designer.user_id) is True
    assert controller.saved_count == 1
    assert "only JPG and PNG" in controller.errors[0]


def test_renamed_non_image_is_rejected(designer, project):
    controller = UploadPhotoController()
    files = [upload("virus.png", b"MZ this is not an image")]
    assert controller.upload_photos(project.project_id, files, designer.user_id) is False
    assert "not a valid image" in controller.errors[0]


def test_file_over_10mb_is_rejected(designer, project):
    too_big = PNG_BYTES + b"\x00" * ProjectPhoto.MAX_BYTES
    controller = UploadPhotoController()
    assert controller.upload_photos(project.project_id, [upload("big.png", too_big)], designer.user_id) is False
    assert "10MB" in controller.errors[0]


def test_cannot_upload_to_another_designers_project(other_designer, project):
    controller = UploadPhotoController()
    assert controller.upload_photos(project.project_id, [upload("a.png", PNG_BYTES)], other_designer.user_id) is False
    assert controller.errors == ["Project not found"]


def test_no_files_selected(designer, project):
    controller = UploadPhotoController()
    assert controller.upload_photos(project.project_id, [], designer.user_id) is False
