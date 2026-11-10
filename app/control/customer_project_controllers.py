from app.entity.project import Project
from app.entity.user_account import UserAccount
from app.entity.project_report import ProjectReport


# UC31 View Project Details

class ViewProjectDetailsController:
    def __init__(self):
        self.errors = []

    # check if the selected project is available for customers to view
    def get_project_details(self, project_id):
        project = Project.find_by_id(project_id)
        
        # do not show projects that are missing or removed
        if project is None or project.status != "active":
            self.errors = ["Project unavailable"]
            return None

        # make sure the project belongs to an active interior designer
        designer = UserAccount.find_by_id(project.designer_id)
        if (designer is None or designer.role != UserAccount.INTERIOR_DESIGNER or not designer.is_active()):
            self.errors = ["Project unavailable"]
            return None

        return project


# UC37 Report Inappropriate Project

class ReportProjectController:
    def __init__(self):
        self.errors = []

    # check the report details before saving it to the database
    def report_project(self, customer_id, project_id, reason, details=""):
        self.errors = []

        # remove extra spaces from customers' answers
        reason = (reason or "").strip()
        details = (details or "").strip()

        # make sure that customers have selected a reason
        if not reason:
            self.errors = ["Please select a reason"]
            return False

        if reason not in ProjectReport.VALID_REASONS:
            self.errors = ["Please select a valid reason"]
            return False

        # limit the additional details to 1000 characters
        if len(details) > 1000:
            self.errors = ["Details must be 1000 characters or fewer"]
            return False

        # check that the report is submitted by an active customer
        customer = UserAccount.find_by_id(customer_id)

        if (customer is None or customer.role != UserAccount.CUSTOMER or not customer.is_active()):
            self.errors = ["Only active customers can report projects"]
            return False

        # reuse UC31 to check if the reported project is still available
        project = ViewProjectDetailsController().get_project_details(project_id)

        if project is None:
            self.errors = ["Project unavailable"]
            return False

        # create the report using the details entered by the customer
        report = ProjectReport(
            customer_id, project_id, reason, details
        )

        # save the report and return an error if it fails
        if not report.submit():
            self.errors = ["Unable to submit report. Please try again."]
            return False

        return True