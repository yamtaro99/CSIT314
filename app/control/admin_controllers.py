from app.entity.interior_designer import InteriorDesigner
from app.entity.company import Company


def _find_pending(user_id):
    """Return the designer if they exist and are still pending, else None."""
    designer = InteriorDesigner.find_by_id(user_id)
    if designer is None or designer.status != "pending":
        return None
    return designer


class ViewApplicationController:
    def __init__(self):
        self.errors = []

    def get_pending_application(self):
        return InteriorDesigner.find_pending()

    def get_application(self, user_id):
        designer = _find_pending(user_id)
        if designer is None:
            self.errors.append("Application not found or no longer pending")
        return designer
    
    def get_company (self, user_id):
        return Company.find_by_designer(user_id)


class ApproveApplicationController:
    def __init__(self):
        self.errors = []
        self.designer = None

    def approve_application(self, user_id):
        designer = _find_pending(user_id)
        if designer is None:
            self.errors.append("Application not found or no longer pending")
            return False
        self.designer = designer
        return designer.set_status("active")


class RejectApplicationController:
    def __init__(self):
        self.errors = []
        self.designer = None

    def reject_application(self, user_id):
        designer = _find_pending(user_id)
        if designer is None:
            self.errors.append("Application not found or no longer pending")
            return False
        self.designer = designer
        return designer.set_status("deactivated")
