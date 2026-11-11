import pytest
from app.control.platform_mgmt_controllers import UserManagementController


class TestUserManagementController:
    def test_get_users_no_filters(self, client):
        """Get all users with no filters."""
        ctrl = UserManagementController()
        result = ctrl.get_users()
        assert result["total"] >= 0
        assert "users" in result
        assert "page" in result
        assert "per_page" in result
        assert "total_pages" in result

    def test_get_users_role_filter(self, client):
        """Filter users by role."""
        ctrl = UserManagementController()
        result = ctrl.get_users(role_filter="customer")
        for u in result["users"]:
            assert u.role == "customer"

    def test_get_users_status_filter(self, client):
        """Filter users by status."""
        ctrl = UserManagementController()
        result = ctrl.get_users(status_filter="active")
        for u in result["users"]:
            assert u.status == "active"

    def test_get_users_search(self, client):
        """Search users by name/email."""
        ctrl = UserManagementController()
        result = ctrl.get_users(search="test")
        # All returned users should match search
        for u in result["users"]:
            assert "test" in u.name.lower() or "test" in u.email.lower()

    def test_get_users_pagination(self, client):
        """Pagination works correctly."""
        ctrl = UserManagementController()
        result = ctrl.get_users(page=1, per_page=5)
        assert result["page"] == 1
        assert result["per_page"] == 5
        assert len(result["users"]) <= 5

    def test_get_user_detail_exists(self, client):
        """Get detail for existing user."""
        ctrl = UserManagementController()
        # Get first user from db
        from app.db import get_db
        conn = get_db()
        row = conn.execute("SELECT user_id FROM user_account LIMIT 1").fetchone()
        if row:
            detail = ctrl.get_user_detail(row["user_id"])
            assert detail is not None
            assert "user" in detail
            assert "projects" in detail
            assert "reviews" in detail

    def test_get_user_detail_not_found(self, client):
        """Get detail for non-existent user returns None."""
        ctrl = UserManagementController()
        detail = ctrl.get_user_detail(999999)
        assert detail is None

    def test_update_user_status_valid(self, client):
        """Update user status to valid value."""
        ctrl = UserManagementController()
        from app.db import get_db
        conn = get_db()
        row = conn.execute("SELECT user_id FROM user_account LIMIT 1").fetchone()
        if row:
            ok = ctrl.update_user_status(row["user_id"], "suspended")
            assert ok is True
            # Verify update
            updated = conn.execute("SELECT status FROM user_account WHERE user_id = ?", (row["user_id"],)).fetchone()
            assert updated["status"] == "suspended"
            # Restore
            ctrl.update_user_status(row["user_id"], "active")

    def test_update_user_status_invalid(self, client):
        """Invalid status rejected."""
        ctrl = UserManagementController()
        ok = ctrl.update_user_status(1, "invalid_status")
        assert ok is False
        assert len(ctrl.errors) > 0

    def test_get_role_options(self, client):
        """Role options returns expected roles."""
        ctrl = UserManagementController()
        roles = ctrl.get_role_options()
        assert "customer" in roles
        assert "interior_designer" in roles
        assert "user_admin" in roles
        assert "platform_manager" in roles

    def test_get_status_options(self, client):
        """Status options returns expected statuses."""
        ctrl = UserManagementController()
        statuses = ctrl.get_status_options()
        assert "active" in statuses
        assert "pending" in statuses
        assert "suspended" in statuses
        assert "deactivated" in statuses