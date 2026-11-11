from app.entity.project import Project
from app.entity.user_account import UserAccount
from app.entity.project_report import ProjectReport


# UC31 View Project Details

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


# UC37 Report Inappropriate Project

class ReportProjectController:
    def __init__(self):
        self.errors = []

    def report_project(self, customer_id, project_id, reason, details=""):
        self.errors = []

        reason = (reason or "").strip()
        details = (details or "").strip()

        if not reason:
            self.errors = ["Please select a reason"]
            return False

        if reason not in ProjectReport.VALID_REASONS:
            self.errors = ["Please select a valid reason"]
            return False

        if len(details) > 1000:
            self.errors = ["Details must be 1000 characters or fewer"]
            return False

        customer = UserAccount.find_by_id(customer_id)

        if (customer is None or customer.role != UserAccount.CUSTOMER or not customer.is_active()):
            self.errors = ["Only active customers can report projects"]
            return False

        # reuse UC31 to check if the reported project is still available
        project = ViewProjectDetailsController().get_project_details(project_id)

        if project is None:
            self.errors = ["Project unavailable"]
            return False

        report = ProjectReport(
            customer_id, project_id, reason, details
        )

        if not report.submit():
            self.errors = ["Unable to submit report. Please try again."]
            return False

        return True
