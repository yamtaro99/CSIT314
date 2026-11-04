from app.entity.category import Category
from app.entity.portfolio import Portfolio
from app.entity.project import Project
from app.entity.project_photo import ProjectPhoto


class AddProjectController:
    def __init__(self):
        self.errors = []
        self.project = None

    def add_project(self, designer_id, title, description, location, completion_date):
        project = Project(designer_id, title, description, location, completion_date)
        if not project.validate():
            self.errors = project.errors
            return False
        if not project.create():
            self.errors = project.errors or ["Could not save the project"]
            return False
        self.project = project
        return Portfolio(designer_id).add_project(project)


class UploadPhotoController:
    def __init__(self):
        self.errors = []
        self.saved_count = 0

    def upload_photos(self, project_id, files, designer_id):
        project = Portfolio(designer_id).get_project(project_id)
        if project is None:
            self.errors = ["Project not found"]
            return False
        files = [f for f in (files or []) if f and f.filename]
        if not files:
            self.errors = ["Please select at least one photo"]
            return False
        for file in files:
            photo = ProjectPhoto(file=file)
            if project.add_photo(photo):
                self.saved_count += 1
            else:
                self.errors.append(photo.error)
        return self.saved_count > 0


class UpdateProjectController:
    def __init__(self):
        self.errors = []

    def update_project(self, project_id, details, designer_id):
        project = Portfolio(designer_id).get_project(project_id)
        if project is None:
            self.errors = ["Project not found"]
            return False
        if not project.update(details):
            self.errors = project.errors
            return False
        return True


class RemoveProjectController:
    def remove_project(self, project_id, designer_id):
        return Portfolio(designer_id).remove_project(project_id)


class TagProjectController:
    def __init__(self):
        self.errors = []

    def get_categories(self):
        return Category.get_active_categories()

    def tag_project(self, project_id, category_ids, designer_id):
        project = Portfolio(designer_id).get_project(project_id)
        if project is None:
            self.errors = ["Project not found"]
            return False
        try:
            ids = {int(c) for c in (category_ids or [])}
        except (TypeError, ValueError):
            self.errors = ["Invalid category"]
            return False
        if not ids:
            self.errors = ["Select at least one category"]
            return False
        categories = Category.find_active_by_ids(ids)
        if len(categories) != len(ids):
            self.errors = ["One or more categories are no longer available"]
            return False
        return project.set_categories(categories)
