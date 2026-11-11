import pytest
from dataclasses import dataclass
from app.control.platform_mgmt_controllers import IDPQueueController, PendingProjectItem
from app.entity.user_account import UserAccount
from app.entity.category import Category
from app.db import get_db, now


PASSWORD = "Test-Password-1"


def make_user(role, email=None, status="active", name="Test User"):
    account = UserAccount(email=email or f"{role}@test.local", name=name, role=role, status=status)
    account.set_password(PASSWORD)
    assert account.create()
    return account


def seed_pending_projects(app):
    """Seed pending projects for IDP queue tests."""
    with app.app_context():
        # Create a pending designer
        pending_designer = make_user(UserAccount.INTERIOR_DESIGNER, "pending_designer@test.local", status="pending", name="Pending Designer")
        
        # Create active designer for comparison
        active_designer = make_user(UserAccount.INTERIOR_DESIGNER, "active_designer@test.local", name="Active Designer")
        
        # Create categories
        cat1 = Category(name="Modern")
        cat1.create()
        cat2 = Category(name="Kitchen")
        cat2.create()
        
        conn = get_db()
        
        # Add pending projects
        for i, (title, desc) in enumerate([
            ("Minimalist Kitchen", "Clean minimalist kitchen"),
            ("Japandi Living Room", "Warm Japandi style"),
            ("Industrial Loft", "Exposed brick and metal"),
        ]):
            conn.execute(
                """INSERT INTO project (designer_id, title, description, location, completion_date,
                   status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)""",
                (pending_designer.user_id, title, desc, "Tampines", "2025-12-31", now(), now())
            )
            pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute("INSERT INTO project_category (project_id, category_id) VALUES (?, ?)", (pid, cat1.category_id))
            conn.execute("INSERT INTO project_category (project_id, category_id) VALUES (?, ?)", (pid, cat2.category_id))
        
        # Add an active project (not pending)
        conn.execute(
            """INSERT INTO project (designer_id, title, description, location, completion_date,
               status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'active', ?, ?)""",
            (active_designer.user_id, "Active Project", "Already approved", "Punggol", "2025-12-31", now(), now())
        )
        
        conn.commit()


class TestIDPQueueController:
    @pytest.fixture(autouse=True)
    def setup(self, app):
        seed_pending_projects(app)
        self.ctrl = IDPQueueController()

    def test_get_pending_projects_with_data(self, app):
        """Get pending projects with seeded data."""
        result = self.ctrl.get_pending_projects()
        # 3 pending projects seeded
        assert result["total"] == 3
        assert len(result["projects"]) == 3
        for p in result["projects"]:
            assert isinstance(p, PendingProjectItem)
            assert p.project_id > 0
            assert p.title
            assert p.designer_name == "Pending Designer"
            assert p.designer_email == "pending_designer@test.local"

    def test_get_pending_projects_pagination(self, app):
        """Pagination works for pending projects."""
        result = self.ctrl.get_pending_projects(page=1, per_page=2)
        assert result["page"] == 1
        assert result["per_page"] == 2
        assert len(result["projects"]) == 2
        assert result["total_pages"] == 2  # 3 total / 2 per page = 2 pages

    def test_get_pending_projects_page_2(self, app):
        """Page 2 returns remaining projects."""
        result = self.ctrl.get_pending_projects(page=2, per_page=2)
        assert result["page"] == 2
        assert len(result["projects"]) == 1

    def test_get_project_detail_exists(self, app):
        """Get detail for existing pending project."""
        conn = get_db()
        row = conn.execute(
            "SELECT project_id FROM project WHERE status = 'pending' LIMIT 1"
        ).fetchone()
        detail = self.ctrl.get_project_detail(row["project_id"])
        assert detail is not None
        assert detail["project_id"] == row["project_id"]
        assert "categories" in detail
        assert "photos" in detail
        assert detail["designer_name"] == "Pending Designer"

    def test_get_project_detail_not_found(self, app):
        """Get detail for non-existent project returns None."""
        detail = self.ctrl.get_project_detail(999999)
        assert detail is None

    def test_approve_project(self, app):
        """Approve a pending project."""
        conn = get_db()
        row = conn.execute(
            "SELECT project_id FROM project WHERE status = 'pending' LIMIT 1"
        ).fetchone()
        pid = row["project_id"]
        ok = self.ctrl.approve_project(pid)
        assert ok is True
        # Verify status changed
        updated = conn.execute(
            "SELECT status FROM project WHERE project_id = ?", (pid,)
        ).fetchone()
        assert updated["status"] == "active"

    def test_reject_project(self, app):
        """Reject a pending project."""
        conn = get_db()
        row = conn.execute(
            "SELECT project_id FROM project WHERE status = 'pending' LIMIT 1"
        ).fetchone()
        pid = row["project_id"]
        ok = self.ctrl.reject_project(pid)
        assert ok is True
        # Verify status changed
        updated = conn.execute(
            "SELECT status FROM project WHERE project_id = ?", (pid,)
        ).fetchone()
        assert updated["status"] == "rejected"

    def test_approve_nonexistent_project(self, app):
        """Approve non-existent project returns False."""
        ok = self.ctrl.approve_project(999999)
        assert ok is False

    def test_reject_nonexistent_project(self, app):
        """Reject non-existent project returns False."""
        ok = self.ctrl.reject_project(999999)
        assert ok is False

    def test_approve_already_processed_project(self, app):
        """Cannot approve already approved project."""
        conn = get_db()
        # Find an active project (already approved)
        row = conn.execute(
            "SELECT project_id FROM project WHERE status = 'active' LIMIT 1"
        ).fetchone()
        ok = self.ctrl.approve_project(row["project_id"])
        # Should fail because status is not 'pending'
        assert ok is False

    def test_reject_already_processed_project(self, app):
        """Cannot reject already rejected project."""
        conn = get_db()
        # First reject a project to get a rejected one
        row = conn.execute(
            "SELECT project_id FROM project WHERE status = 'pending' LIMIT 1"
        ).fetchone()
        self.ctrl.reject_project(row["project_id"])
        
        # Now try to reject it again
        ok = self.ctrl.reject_project(row["project_id"])
        # Should fail because status is not 'pending'
        assert ok is False