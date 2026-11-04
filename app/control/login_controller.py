from app.entity.user_account import UserAccount


class LoginController:
    def __init__(self):
        self.error = None

    def login(self, email, password):
        account = UserAccount.find_by_email(email)
        if account is None or not account.check_password(password or ""):
            self.error = "Incorrect email or password"
            return None
        if account.status == "pending":
            self.error = "Your account is waiting for approval"
            return None
        if not account.is_active():
            self.error = "Your account is not active. Please contact the User Admin"
            return None
        return account
