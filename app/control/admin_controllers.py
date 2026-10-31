from app.entity.interior_designer import InteriorDesigner


class IDApplicationController:
    def __init__(self):
        self.errors = []
        self.designer = None

    def get_pending_application(self):
        return InteriorDesigner.find_pending()

    def get_application(self, user_id):
        designer = InteriorDesigner.find_by_id(user_id)
        if designer is None or designer.status != "pending":
            return None
        return designer

    def _load_pending(self, user_id):
        designer = self.get_application(user_id)
        if designer is None:
            self.errors.append("Application not found or no longer pending")
        return designer

    def approve_application(self, user_id):
        designer = self._load_pending(user_id)
        if designer is None:
            return False
        self.designer = designer
        return designer.set_status("active")

    def reject_application(self, user_id):
        designer = self._load_pending(user_id)
        if designer is None:
            return False
        self.designer = designer
        return designer.set_status("deactivated")

    def request_additional_docs(self, user_id, remarks):
        remarks = (remarks or "").strip()
        if not remarks:
            self.errors.append("Please state which documents are needed")
            return False
        designer = self._load_pending(user_id)
        if designer is None:
            return False
        self.designer = designer
        # TODO: save the remarks once the database has a place for them
        return True