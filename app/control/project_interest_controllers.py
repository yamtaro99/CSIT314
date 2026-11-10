from datetime import date, timedelta

from app.control.customer_project_controllers import ViewProjectDetailsController
from app.entity.project import Project
from app.entity.project_metrics import ProjectMetrics
from app.entity.project_shortlist import ProjectShortlist
from app.entity.project_shortlist_event import ProjectShortlistEvent
from app.entity.project_view import ProjectView
from app.entity.user_account import UserAccount
from app.entity.weekly_interest import WeeklyChart, WeeklyInterest, WeeklyInterestReport


def _active_designer(designer_id):
    designer = UserAccount.find_by_id(designer_id)
    return (designer is not None and designer.role == UserAccount.INTERIOR_DESIGNER
            and designer.is_active())


class TrackProjectShortlistController:
    def __init__(self):
        self.errors = []
        self.result = None

    def set_shortlisted(self, customer_id, project_id, action):
        self.errors = []
        self.result = None
        customer = UserAccount.find_by_id(customer_id)
        if customer is None or customer.role != UserAccount.CUSTOMER or not customer.is_active():
            self.errors.append("Only active customers can shortlist projects")
            return False
        if ViewProjectDetailsController().get_project_details(project_id) is None:
            self.errors.append("Project unavailable")
            return False
        if action == "add":
            self.result = "added" if ProjectShortlist.add(customer_id, project_id) else "already_saved"
            return True
        if action == "remove":
            self.result = "removed" if ProjectShortlist.remove(customer_id, project_id) else "not_saved"
            return True
        self.errors.append("Invalid shortlist action")
        return False


class ViewFavouritesController:
    def get_favourites(self, customer_id):
        customer = UserAccount.find_by_id(customer_id)
        if customer is None or customer.role != UserAccount.CUSTOMER or not customer.is_active():
            return None
        return ProjectShortlist.favourites_for_customer(customer_id)


class ViewShortlistCountsController:
    def __init__(self):
        self.errors = []

    def get_counts(self, designer_id):
        self.errors = []
        if not _active_designer(designer_id):
            self.errors.append("Only active interior designers can view project interest")
            return None
        projects = Project.find_active_by_designer(designer_id)
        counts = ProjectShortlist.counts_by_project([p.project_id for p in projects])
        return [ProjectMetrics(project=p, shortlist_count=counts.get(p.project_id, 0))
                for p in projects]


class ViewWeeklyInterestTrendsController:
    def __init__(self):
        self.errors = []

    def get_trends(self, designer_id, project_id=None, today=None, number_of_weeks=8):
        self.errors = []
        if not _active_designer(designer_id):
            self.errors.append("Only active interior designers can view project interest")
            return None
        projects = Project.find_active_by_designer(designer_id)
        owned_ids = [p.project_id for p in projects]
        if project_id is not None:
            if project_id not in owned_ids:
                self.errors.append("Project unavailable")
                return None
            selected_ids = [project_id]
        else:
            selected_ids = owned_ids

        current_day = today or date.today()
        current_monday = current_day - timedelta(days=current_day.weekday())
        first_monday = current_monday - timedelta(weeks=number_of_weeks - 1)
        end_monday = current_monday + timedelta(weeks=1)
        views = ProjectView.weekly_counts(selected_ids, first_monday, end_monday)
        shortlists = ProjectShortlistEvent.weekly_add_counts(selected_ids, first_monday, end_monday)
        weeks = []
        for index in range(number_of_weeks):
            monday = first_monday + timedelta(weeks=index)
            weeks.append(WeeklyInterest(
                week_start=monday.isoformat(), label=monday.strftime("%d %b"),
                views=views.get(monday, 0), shortlist_adds=shortlists.get(monday, 0),
            ))
        return WeeklyInterestReport(
            weeks=weeks,
            views_chart=WeeklyChart(weeks, "views", "Weekly Views"),
            shortlists_chart=WeeklyChart(weeks, "shortlist_adds", "Weekly New Shortlists"),
        )
