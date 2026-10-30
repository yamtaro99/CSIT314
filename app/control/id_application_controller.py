from app.entity.interior_designer import InteriorDesigner


class IDApplicationController:
    def __init__(self):
        self.errors = []

    def get_pending_application(self):
        return InteriorDesigner.find_pending()

    def approve_application(self, user_id):
        designer = InteriorDesigner.find_by_id(user_id)
        if designer is None:
            self.errors.append("Application not found")
            return False
        if designer.status != "pending":
            self.errors.append("Only pending applications can be approved")
            return False
        return designer.set_status("active")