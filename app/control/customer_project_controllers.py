from app.entity.project import Project
from app.entity.user_account import UserAccount


class ViewProjectDetailsController:
    def __init__(self):
        self.errors = []

    def get_project_details(self, project_id):
        project = Project.find_by_id(project_id)
        if project is None or project.status != "active":
            self.errors = ["Project unavailable"]
            return None

        designer = UserAccount.find_by_id(project.designer_id)
        if (designer is None or designer.role != UserAccount.INTERIOR_DESIGNER or not designer.is_active()):
            self.errors = ["Project unavailable"]
            return None

        return project