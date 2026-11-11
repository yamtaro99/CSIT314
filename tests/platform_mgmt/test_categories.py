import pytest
from app.entity.category import Category
from app.entity.user_account import UserAccount
from app.control.platform_mgmt_controllers import CategoryController, PlatformDashboardController


PASSWORD = "Test-Password-1"


def make_user(role, email=None, status="active", name="Test User"):
    account = UserAccount(email=email or f"{role}@test.local", name=name, role=role, status=status)
    account.set_password(PASSWORD)
    assert account.create()
    return account


def login(client, email, password=PASSWORD):
    return client.post("/login", data={"email": email, "password": password})


class TestCategoryController:
    def test_create_category_succeeds(self, app):
        ctrl = CategoryController()
        cat = ctrl.create_category("Test Category")
        assert cat is not None
        assert cat.name == "Test Category"
        assert cat.is_active is True
        assert cat.category_id is not None

    def test_create_category_empty_name_fails(self, app):
        ctrl = CategoryController()
        cat = ctrl.create_category("")
        assert cat is None
        assert "Category name cannot be empty" in ctrl.errors

    def test_create_duplicate_category_fails(self, app):
        ctrl = CategoryController()
        ctrl.create_category("Unique Name")
        cat = ctrl.create_category("Unique Name")
        assert cat is None
        assert "already exists" in ctrl.errors[0]

    def test_get_all_categories_returns_both_active_and_inactive(self, app):
        ctrl = CategoryController()
        ctrl.create_category("Active Cat")
        ctrl.create_category("Inactive Cat", is_active=False)
        cats = ctrl.get_all_categories()
        names = {c.name for c in cats}
        assert "Active Cat" in names
        assert "Inactive Cat" in names
        # Inactive should come after active (ORDER BY is_active DESC)
        active_first = [c for c in cats if c.is_active]
        inactive_first = [c for c in cats if not c.is_active]
        assert len(active_first) > 0
        assert len(inactive_first) > 0

    def test_get_active_categories_excludes_inactive(self, app):
        ctrl = CategoryController()
        ctrl.create_category("Active Cat")
        ctrl.create_category("Inactive Cat", is_active=False)
        active = ctrl.get_active_categories()
        assert len(active) == 1
        assert active[0].name == "Active Cat"

    def test_update_category_succeeds(self, app):
        ctrl = CategoryController()
        cat = ctrl.create_category("Original Name")
        assert ctrl.update_category(cat.category_id, "Updated Name", False)
        # Verify
        conn = __import__("app.db", fromlist=["get_db"]).get_db()
        row = conn.execute("SELECT * FROM category WHERE category_id = ?", (cat.category_id,)).fetchone()
        assert row["name"] == "Updated Name"
        assert row["is_active"] == 0

    def test_update_category_empty_name_fails(self, app):
        ctrl = CategoryController()
        cat = ctrl.create_category("Original")
        assert not ctrl.update_category(cat.category_id, "", True)
        assert "Category name cannot be empty" in ctrl.errors

    def test_update_category_duplicate_name_fails(self, app):
        ctrl = CategoryController()
        cat1 = ctrl.create_category("Name One")
        cat2 = ctrl.create_category("Name Two")
        assert not ctrl.update_category(cat2.category_id, "Name One", True)
        assert "already exists" in ctrl.errors[0]

    def test_delete_category_unused_hard_deletes(self, app):
        ctrl = CategoryController()
        cat = ctrl.create_category("Unused Category")
        result = ctrl.delete_category(cat.category_id)
        assert result == "deleted"
        # Verify gone
        conn = __import__("app.db", fromlist=["get_db"]).get_db()
        row = conn.execute("SELECT * FROM category WHERE category_id = ?", (cat.category_id,)).fetchone()
        assert row is None

    def test_delete_category_in_use_soft_deletes(self, app):
        # Need a designer and project using the category
        designer = make_user(UserAccount.INTERIOR_DESIGNER, "designer@test.local")
        ctrl = CategoryController()
        cat = ctrl.create_category("Used Category")
        # Create project with this category
        from app.entity.project import Project
        proj = Project(designer.user_id, "Test Project", "Desc", "Location", "2025-12-31")
        proj.create()
        conn = __import__("app.db", fromlist=["get_db"]).get_db()
        conn.execute("INSERT INTO project_category (project_id, category_id) VALUES (?, ?)",
                     (proj.project_id, cat.category_id))
        conn.commit()
        # Now delete
        result = ctrl.delete_category(cat.category_id)
        assert result == "deactivated"
        # Verify inactive
        row = conn.execute("SELECT * FROM category WHERE category_id = ?", (cat.category_id,)).fetchone()
        assert row["is_active"] == 0


class TestPlatformDashboardController:
    def test_get_metrics_returns_expected_keys(self, app):
        ctrl = PlatformDashboardController()
        metrics = ctrl.get_metrics()
        expected_keys = {
            "total_projects", "total_designers", "total_customers",
            "pending_designers", "pending_projects", "total_categories",
            "recent_projects", "recent_users"
        }
        assert set(metrics.keys()) == expected_keys

    def test_metrics_counts_are_correct(self, app):
        make_user(UserAccount.INTERIOR_DESIGNER, "d1@test.local")
        make_user(UserAccount.INTERIOR_DESIGNER, "d2@test.local", status="pending")
        make_user(UserAccount.CUSTOMER, "c1@test.local")
        ctrl = PlatformDashboardController()
        metrics = ctrl.get_metrics()
        assert metrics["total_designers"] == 1
        assert metrics["pending_designers"] == 1
        assert metrics["total_customers"] == 1


class TestPlatformMgmtAccessControl:
    def test_anonymous_redirected_to_login(self, client):
        resp = client.get("/platform/")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_customer_cannot_access_platform_dashboard(self, client, app):
        customer = make_user(UserAccount.CUSTOMER, "customer@test.local")
        login(client, customer.email)
        resp = client.get("/platform/")
        assert resp.status_code == 403

    def test_designer_cannot_access_platform_dashboard(self, client, app):
        designer = make_user(UserAccount.INTERIOR_DESIGNER, "designer@test.local")
        login(client, designer.email)
        resp = client.get("/platform/")
        assert resp.status_code == 403

    def test_user_admin_cannot_access_platform_dashboard(self, client, app):
        admin = make_user(UserAccount.USER_ADMIN, "admin@test.local")
        login(client, admin.email)
        resp = client.get("/platform/")
        assert resp.status_code == 403

    def test_platform_manager_can_access_dashboard(self, client, app):
        pm = make_user(UserAccount.PLATFORM_MANAGER, "pm@test.local")
        login(client, pm.email)
        resp = client.get("/platform/")
        assert resp.status_code == 200
        assert b"Platform Dashboard" in resp.data

    def test_platform_manager_can_access_categories(self, client, app):
        pm = make_user(UserAccount.PLATFORM_MANAGER, "pm@test.local")
        login(client, pm.email)
        resp = client.get("/platform/categories")
        assert resp.status_code == 200
        assert b"Manage Categories" in resp.data

    def test_platform_manager_can_create_category(self, client, app):
        pm = make_user(UserAccount.PLATFORM_MANAGER, "pm@test.local")
        login(client, pm.email)
        resp = client.post("/platform/categories/create", data={
            "name": "New Test Category",
            "is_active": "1"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Category" in resp.data
        assert b"created successfully" in resp.data
        # Verify in DB
        conn = __import__("app.db", fromlist=["get_db"]).get_db()
        row = conn.execute("SELECT * FROM category WHERE name = ?", ("New Test Category",)).fetchone()
        assert row is not None
        assert row["is_active"] == 1

    def test_platform_manager_can_edit_category(self, client, app):
        pm = make_user(UserAccount.PLATFORM_MANAGER, "pm@test.local")
        login(client, pm.email)
        # Create first
        client.post("/platform/categories/create", data={"name": "To Edit", "is_active": "1"})
        conn = __import__("app.db", fromlist=["get_db"]).get_db()
        cat = conn.execute("SELECT * FROM category WHERE name = ?", ("To Edit",)).fetchone()
        # Edit
        resp = client.post(f"/platform/categories/{cat['category_id']}/edit", data={
            "name": "Edited Name",
            "is_active": "0"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"updated successfully" in resp.data
        # Verify
        row = conn.execute("SELECT * FROM category WHERE category_id = ?", (cat["category_id"],)).fetchone()
        assert row["name"] == "Edited Name"
        assert row["is_active"] == 0

    def test_platform_manager_can_delete_unused_category(self, client, app):
        pm = make_user(UserAccount.PLATFORM_MANAGER, "pm@test.local")
        login(client, pm.email)
        client.post("/platform/categories/create", data={"name": "To Delete", "is_active": "1"})
        conn = __import__("app.db", fromlist=["get_db"]).get_db()
        cat = conn.execute("SELECT * FROM category WHERE name = ?", ("To Delete",)).fetchone()
        resp = client.post(f"/platform/categories/{cat['category_id']}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert b"deleted permanently" in resp.data
        row = conn.execute("SELECT * FROM category WHERE category_id = ?", (cat["category_id"],)).fetchone()
        assert row is None