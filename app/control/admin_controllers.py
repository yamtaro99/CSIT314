from app.entity.interior_designer import InteriorDesigner


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


class RequestAdditionalDocsController:
    def __init__(self):
        self.errors = []
        self.designer = None

    def request_additional_docs(self, user_id, remarks):
        remarks = (remarks or "").strip()
        if not remarks:
            self.errors.append("Please state which documents are needed")
            return False
        designer = _find_pending(user_id)
        if designer is None:
            self.errors.append("Application not found or no longer pending")
            return False
        self.designer = designer
        # TODO: save the remarks once the database has a place for them
        return True

class ApproveApplicationController:
    pass
