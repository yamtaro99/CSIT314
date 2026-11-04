from app.entity.project import Project


class Portfolio:
    def __init__(self, designer_id):
        self.designer_id = designer_id
        self._projects = None

    def get_projects(self):
        if self._projects is None:
            self._projects = Project.find_active_by_designer(self.designer_id)
        return self._projects

    def get_project(self, project_id):
        for project in self.get_projects():
            if project.project_id == project_id:
                return project
        return None

    def add_project(self, project):
        if project.project_id is None or project.designer_id != self.designer_id:
            return False
        if self.get_project(project.project_id) is None:
            self._projects.append(project)
        return True

    def remove_project(self, project_id):
        project = self.get_project(project_id)
        if project is None or not project.mark_removed():
            return False
        self._projects.remove(project)
        return True
