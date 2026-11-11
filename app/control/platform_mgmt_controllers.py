import sqlite3
from dataclasses import dataclass
from app.entity.category import Category
from app.entity.user_account import UserAccount
from app.db import get_db, now


class PlatformDashboardController:
    def __init__(self):
        self.errors = []

    def get_metrics(self):
        """Return key platform metrics for the dashboard."""
        conn = get_db()
        try:
            metrics = {}

            # Total projects
            metrics["total_projects"] = conn.execute(
                "SELECT COUNT(*) FROM project WHERE status = 'active'"
            ).fetchone()[0]

            # Total users by role
            metrics["total_designers"] = conn.execute(
                "SELECT COUNT(*) FROM user_account WHERE role = 'interior_designer' AND status = 'active'"
            ).fetchone()[0]

            metrics["total_customers"] = conn.execute(
                "SELECT COUNT(*) FROM user_account WHERE role = 'customer' AND status = 'active'"
            ).fetchone()[0]

            metrics["pending_designers"] = conn.execute(
                "SELECT COUNT(*) FROM user_account WHERE role = 'interior_designer' AND status = 'pending'"
            ).fetchone()[0]

            # Pending IDPs (projects awaiting moderation)
            metrics["pending_projects"] = conn.execute(
                "SELECT COUNT(*) FROM project WHERE status = 'pending'"
            ).fetchone()[0]

            # Total categories
            metrics["total_categories"] = conn.execute(
                "SELECT COUNT(*) FROM category WHERE is_active = 1"
            ).fetchone()[0]

            # Recent activity: last 10 project creations
            recent_projects = conn.execute(
                "SELECT p.project_id, p.title, p.created_at, u.name as designer_name "
                "FROM project p "
                "JOIN user_account u ON p.designer_id = u.user_id "
                "WHERE p.status = 'active' "
                "ORDER BY p.created_at DESC LIMIT 10"
            ).fetchall()
            metrics["recent_projects"] = [dict(r) for r in recent_projects]

            # Recent user registrations
            recent_users = conn.execute(
                "SELECT user_id, name, role, status, created_at "
                "FROM user_account "
                "ORDER BY created_at DESC LIMIT 10"
            ).fetchall()
            metrics["recent_users"] = [dict(r) for r in recent_users]

            return metrics

        except Exception as e:
            self.errors.append(f"Failed to load dashboard metrics: {e}")
            return {}


class CategoryController:
    def __init__(self):
        self.errors = []

    def get_all_categories(self):
        """Return all categories (active and inactive) for management view."""
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM category ORDER BY is_active DESC, name"
        ).fetchall()
        return [Category._from_row(r) for r in rows]

    def get_active_categories(self):
        """Return only active categories for project tagging."""
        return Category.get_active_categories()

    def create_category(self, name, is_active=True):
        """Create a new category."""
        if not (name or "").strip():
            self.errors.append("Category name cannot be empty")
            return None

        # Parse checkbox value: "on", "1", "true" (case-insensitive) -> True; anything else -> False
        if isinstance(is_active, str):
            is_active = is_active.lower() in ("1", "on", "true", "yes")
        else:
            is_active = bool(is_active)

        cat = Category(name=name.strip(), is_active=is_active)
        try:
            if not cat.create():
                self.errors.append("Failed to create category")
                return None
        except sqlite3.IntegrityError:
            self.errors.append("A category with this name already exists")
            return None
        return cat

    def update_category(self, category_id, name, is_active):
        """Update an existing category."""
        if not (name or "").strip():
            self.errors.append("Category name cannot be empty")
            return False

        # Parse checkbox value: "on", "1", "true" (case-insensitive) -> True; anything else -> False
        if isinstance(is_active, str):
            is_active = is_active.lower() in ("1", "on", "true", "yes")
        else:
            is_active = bool(is_active)

        conn = get_db()
        try:
            # Check if another category has this name
            existing = conn.execute(
                "SELECT category_id FROM category WHERE name = ? AND category_id != ?",
                (name.strip(), category_id)
            ).fetchone()
            if existing:
                self.errors.append("A category with this name already exists")
                return False

            conn.execute(
                "UPDATE category SET name = ?, is_active = ? WHERE category_id = ?",
                (name.strip(), int(is_active), category_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            self.errors.append(f"Failed to update category: {e}")
            return False

    def delete_category(self, category_id):
        """Soft delete (deactivate) a category. Hard delete only if unused."""
        conn = get_db()
        try:
            # Check if category is used by any active projects
            in_use = conn.execute(
                "SELECT 1 FROM project_category pc "
                "JOIN project p ON pc.project_id = p.project_id "
                "WHERE pc.category_id = ? AND p.status = 'active'",
                (category_id,)
            ).fetchone()

            if in_use:
                # Soft delete - just deactivate
                conn.execute(
                    "UPDATE category SET is_active = 0 WHERE category_id = ?",
                    (category_id,)
                )
                conn.commit()
                self.errors.append("Category is in use; deactivated instead of deleted")
                return "deactivated"
            else:
                # Hard delete - safe to remove
                conn.execute("DELETE FROM category WHERE category_id = ?", (category_id,))
                conn.commit()
                return "deleted"
        except Exception as e:
            conn.rollback()
            self.errors.append(f"Failed to delete category: {e}")
            return False


@dataclass
class UserListItem:
    user_id: int
    email: str
    name: str
    role: str
    status: str
    created_at: str
    last_login: str | None
    project_count: int


class UserManagementController:
    def __init__(self):
        self.errors = []

    def get_users(self, role_filter=None, status_filter=None, search=None, page=1, per_page=20):
        """Return paginated, filtered list of users."""
        conn = get_db()
        try:
            where_clauses = []
            params = []

            if role_filter and role_filter in UserAccount.ROLES:
                where_clauses.append("role = ?")
                params.append(role_filter)

            if status_filter and status_filter in ("active", "pending", "suspended", "deactivated"):
                where_clauses.append("status = ?")
                params.append(status_filter)

            if search:
                where_clauses.append("(name LIKE ? OR email LIKE ?)")
                params.extend([f"%{search}%", f"%{search}%"])

            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Total count for pagination
            total = conn.execute(
                f"SELECT COUNT(*) FROM user_account {where_sql}", params
            ).fetchone()[0]

            # Paginated results with project count
            offset = (page - 1) * per_page
            params_with_limit = params + [per_page, offset]
            rows = conn.execute(
                f"""
                SELECT u.user_id, u.email, u.name, u.role, u.status, u.created_at,
                       u.last_login,
                       (SELECT COUNT(*) FROM project p WHERE p.designer_id = u.user_id AND p.status = 'active') as project_count
                FROM user_account u
                {where_sql}
                ORDER BY u.created_at DESC
                LIMIT ? OFFSET ?
                """,
                params_with_limit
            ).fetchall()

            users = [UserListItem(**dict(r)) for r in rows]
            return {
                "users": users,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
            }

        except Exception as e:
            self.errors.append(f"Failed to load users: {e}")
            return {"users": [], "total": 0, "page": 1, "per_page": per_page, "total_pages": 0}

    def get_user_detail(self, user_id):
        """Get detailed view of a single user including their projects."""
        conn = get_db()
        try:
            user_row = conn.execute(
                "SELECT * FROM user_account WHERE user_id = ?", (user_id,)
            ).fetchone()
            if not user_row:
                return None

            user = UserAccount._from_row(user_row)

            # Get projects if designer
            projects = []
            if user.role == UserAccount.INTERIOR_DESIGNER:
                proj_rows = conn.execute(
                    "SELECT project_id, title, status, created_at FROM project WHERE designer_id = ? ORDER BY created_at DESC",
                    (user_id,)
                ).fetchall()
                projects = [dict(r) for r in proj_rows]

            # Get reviews if designer
            reviews = []
            if user.role == UserAccount.INTERIOR_DESIGNER:
                rev_rows = conn.execute(
                    "SELECT review_id, rating, comment, status, submitted_at FROM customer_review WHERE designer_id = ? ORDER BY submitted_at DESC",
                    (user_id,)
                ).fetchall()
                reviews = [dict(r) for r in rev_rows]

            # Get shortlist count if customer
            shortlist_count = 0
            if user.role == UserAccount.CUSTOMER:
                shortlist_count = conn.execute(
                    "SELECT COUNT(*) FROM project_shortlist WHERE customer_id = ?", (user_id,)
                ).fetchone()[0]

            return {
                "user": user,
                "projects": projects,
                "reviews": reviews,
                "shortlist_count": shortlist_count,
            }

        except Exception as e:
            self.errors.append(f"Failed to load user detail: {e}")
            return None

    def update_user_status(self, user_id, new_status):
        """Update a user's status (active/pending/suspended/deactivated)."""
        valid_statuses = ("active", "pending", "suspended", "deactivated")
        if new_status not in valid_statuses:
            self.errors.append(f"Invalid status: {new_status}")
            return False

        conn = get_db()
        try:
            conn.execute(
                "UPDATE user_account SET status = ? WHERE user_id = ?",
                (new_status, user_id)
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            self.errors.append(f"Failed to update user status: {e}")
            return False

    def get_role_options(self):
        return UserAccount.ROLES

    def get_status_options(self):
        return ("active", "pending", "suspended", "deactivated")


@dataclass
class PendingProjectItem:
    project_id: int
    title: str
    designer_name: str
    designer_email: str
    category_names: str
    location: str
    completion_date: str
    created_at: str


class IDPQueueController:
    def __init__(self):
        self.errors = []

    def get_pending_projects(self, page=1, per_page=20):
        """Return paginated list of pending projects awaiting moderation."""
        conn = get_db()
        try:
            # Total count
            total = conn.execute(
                "SELECT COUNT(*) FROM project WHERE status = 'pending'"
            ).fetchone()[0]

            offset = (page - 1) * per_page
            rows = conn.execute(
                """
                SELECT p.project_id, p.title, p.location, p.completion_date, p.created_at,
                       u.name as designer_name, u.email as designer_email,
                       GROUP_CONCAT(c.name, ', ') as category_names
                FROM project p
                JOIN user_account u ON p.designer_id = u.user_id
                LEFT JOIN project_category pc ON p.project_id = pc.project_id
                LEFT JOIN category c ON pc.category_id = c.category_id
                WHERE p.status = 'pending'
                GROUP BY p.project_id
                ORDER BY p.created_at ASC
                LIMIT ? OFFSET ?
                """,
                (per_page, offset)
            ).fetchall()

            projects = [PendingProjectItem(**dict(r)) for r in rows]
            return {
                "projects": projects,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
            }
        except Exception as e:
            self.errors.append(f"Failed to load pending projects: {e}")
            return {"projects": [], "total": 0, "page": 1, "per_page": per_page, "total_pages": 0}

    def get_project_detail(self, project_id):
        """Get full detail of a pending project for review."""
        conn = get_db()
        try:
            # Get project with designer info
            row = conn.execute(
                """
                SELECT p.*, u.name as designer_name, u.email as designer_email,
                       u.user_id as designer_id
                FROM project p
                JOIN user_account u ON p.designer_id = u.user_id
                WHERE p.project_id = ?
                """,
                (project_id,)
            ).fetchone()
            if not row:
                return None

            project = dict(row)

            # Get categories
            cat_rows = conn.execute(
                """
                SELECT c.category_id, c.name
                FROM category c
                JOIN project_category pc ON c.category_id = pc.category_id
                WHERE pc.project_id = ?
                """,
                (project_id,)
            ).fetchall()
            project["categories"] = [dict(r) for r in cat_rows]

            # Get photos
            photo_rows = conn.execute(
                "SELECT photo_id, file_url, caption, uploaded_at FROM project_photo WHERE project_id = ?",
                (project_id,)
            ).fetchall()
            project["photos"] = [dict(r) for r in photo_rows]

            return project

        except Exception as e:
            self.errors.append(f"Failed to load project detail: {e}")
            return None

    def approve_project(self, project_id):
        """Approve a pending project (status -> active)."""
        conn = get_db()
        try:
            cursor = conn.execute(
                "UPDATE project SET status = 'active', updated_at = ? WHERE project_id = ? AND status = 'pending'",
                (now(), project_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            self.errors.append(f"Failed to approve project: {e}")
            return False

    def reject_project(self, project_id):
        """Reject a pending project (status -> rejected)."""
        conn = get_db()
        try:
            cursor = conn.execute(
                "UPDATE project SET status = 'rejected', updated_at = ? WHERE project_id = ? AND status = 'pending'",
                (now(), project_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            self.errors.append(f"Failed to reject project: {e}")
            return False


@dataclass
class ReportSummary:
    period_start: str
    period_end: str
    projects_created: int
    projects_approved: int
    projects_rejected: int
    users_registered: int
    designers_registered: int
    customers_registered: int
    total_enquiries: int
    total_views: int
    total_shortlists: int


class ReportsController:
    def __init__(self):
        self.errors = []

    def _get_date_bounds(self, period_type, custom_start=None, custom_end=None):
        """Return (start_date, end_date) strings for the given period type."""
        from datetime import datetime, timedelta
        now = datetime.now()

        if period_type == "daily":
            # Yesterday by default
            target = now - timedelta(days=1)
            start = target.replace(hour=0, minute=0, second=0, microsecond=0)
            end = target.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif period_type == "weekly":
            # Last 7 days
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period_type == "monthly":
            # Last 30 days
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period_type == "custom" and custom_start and custom_end:
            start = datetime.fromisoformat(custom_start)
            end = datetime.fromisoformat(custom_end)
        else:
            self.errors.append(f"Invalid period type: {period_type}")
            return None, None

        return start.isoformat(), end.isoformat()

    def generate_report(self, period_type, custom_start=None, custom_end=None):
        """Generate a platform activity report for the given period."""
        conn = get_db()
        try:
            start, end = self._get_date_bounds(period_type, custom_start, custom_end)
            if start is None:
                return None

            # Projects created in period
            projects_created = conn.execute(
                "SELECT COUNT(*) FROM project WHERE created_at BETWEEN ? AND ?", (start, end)
            ).fetchone()[0]

            # Projects approved in period
            projects_approved = conn.execute(
                "SELECT COUNT(*) FROM project WHERE status = 'active' AND updated_at BETWEEN ? AND ?", (start, end)
            ).fetchone()[0]

            # Projects rejected in period
            projects_rejected = conn.execute(
                "SELECT COUNT(*) FROM project WHERE status = 'rejected' AND updated_at BETWEEN ? AND ?", (start, end)
            ).fetchone()[0]

            # Users registered in period
            users_registered = conn.execute(
                "SELECT COUNT(*) FROM user_account WHERE created_at BETWEEN ? AND ?", (start, end)
            ).fetchone()[0]

            # Designers registered in period
            designers_registered = conn.execute(
                "SELECT COUNT(*) FROM user_account WHERE role = 'interior_designer' AND created_at BETWEEN ? AND ?", (start, end)
            ).fetchone()[0]

            # Customers registered in period
            customers_registered = conn.execute(
                "SELECT COUNT(*) FROM user_account WHERE role = 'customer' AND created_at BETWEEN ? AND ?", (start, end)
            ).fetchone()[0]

            # Enquiries (project views as proxy for interest)
            total_views = conn.execute(
                "SELECT COUNT(*) FROM project_view WHERE viewed_at BETWEEN ? AND ?", (start, end)
            ).fetchone()[0]

            # Shortlists
            total_shortlists = conn.execute(
                "SELECT COUNT(*) FROM project_shortlist_event WHERE action = 'add' AND event_at BETWEEN ? AND ?", (start, end)
            ).fetchone()[0]

            # Enquiries - using project_view as proxy
            total_enquiries = total_views

            return ReportSummary(
                period_start=start[:19].replace("T", " "),
                period_end=end[:19].replace("T", " "),
                projects_created=projects_created,
                projects_approved=projects_approved,
                projects_rejected=projects_rejected,
                users_registered=users_registered,
                designers_registered=designers_registered,
                customers_registered=customers_registered,
                total_enquiries=total_enquiries,
                total_views=total_views,
                total_shortlists=total_shortlists,
            )
        except Exception as e:
            self.errors.append(f"Failed to generate {period_type} report: {e}")
            return None

    def get_daily_report(self, date=None):
        """Generate daily report for a specific date (defaults to yesterday)."""
        if date:
            return self.generate_report("custom", custom_start=date, custom_end=date)
        return self.generate_report("daily")

    def get_weekly_report(self, start_date=None, end_date=None):
        """Generate weekly report for the last 7 days or custom range."""
        if start_date and end_date:
            return self.generate_report("custom", custom_start=start_date, custom_end=end_date)
        return self.generate_report("weekly")

    def get_monthly_report(self, start_date=None, end_date=None):
        """Generate monthly report for the last 30 days or custom range."""
        if start_date and end_date:
            return self.generate_report("custom", custom_start=start_date, custom_end=end_date)
        return self.generate_report("monthly")


@dataclass
class DesignerPerformanceItem:
    designer_id: int
    name: str
    email: str
    company_name: str | None
    total_projects: int
    active_projects: int
    approval_rate: float
    avg_rating: float | None
    total_reviews: int
    total_views: int
    total_shortlists: int
    joined_at: str


class DesignerPerformanceController:
    def __init__(self):
        self.errors = []

    def get_all_designers(self):
        """Get all interior designers with their performance metrics."""
        conn = get_db()
        try:
            rows = conn.execute(
                """
                SELECT
                    u.user_id,
                    u.name,
                    u.email,
                    u.created_at as joined_at,
                    c.registration_no,
                    c.address as company_name,
                    (SELECT COUNT(*) FROM project p WHERE p.designer_id = u.user_id) as total_projects,
                    (SELECT COUNT(*) FROM project p WHERE p.designer_id = u.user_id AND p.status = 'active') as active_projects,
                    (SELECT COUNT(*) FROM project p WHERE p.designer_id = u.user_id AND p.status = 'rejected') as rejected_projects,
                    (SELECT AVG(r.rating) FROM customer_review r WHERE r.designer_id = u.user_id AND r.status = 'approved') as avg_rating,
                    (SELECT COUNT(*) FROM customer_review r WHERE r.designer_id = u.user_id AND r.status = 'approved') as total_reviews,
                    (SELECT COUNT(*) FROM project_view pv
                     JOIN project p ON pv.project_id = p.project_id
                     WHERE p.designer_id = u.user_id) as total_views,
                    (SELECT COUNT(*) FROM project_shortlist_event pse
                     JOIN project p ON pse.project_id = p.project_id
                     WHERE p.designer_id = u.user_id AND pse.action = 'add') as total_shortlists
                FROM user_account u
                LEFT JOIN company c ON u.user_id = c.designer_id
                WHERE u.role = 'interior_designer'
                ORDER BY u.created_at DESC
                """
            ).fetchall()

            designers = []
            for r in rows:
                total = r["total_projects"]
                rejected = r["rejected_projects"]
                approved = total - rejected if total > 0 else 0
                approval_rate = (approved / total * 100) if total > 0 else 0.0

                designers.append(DesignerPerformanceItem(
                    designer_id=r["user_id"],
                    name=r["name"],
                    email=r["email"],
                    company_name=r["company_name"],
                    total_projects=r["total_projects"],
                    active_projects=r["active_projects"],
                    approval_rate=round(approval_rate, 1),
                    avg_rating=round(r["avg_rating"], 1) if r["avg_rating"] else None,
                    total_reviews=r["total_reviews"],
                    total_views=r["total_views"],
                    total_shortlists=r["total_shortlists"],
                    joined_at=r["joined_at"][:16].replace("T", " ") if r["joined_at"] else "",
                ))
            return designers
        except Exception as e:
            self.errors.append(f"Failed to load designer performance: {e}")
            return []

    def get_designer_detail(self, designer_id):
        """Get detailed performance for a specific designer."""
        conn = get_db()
        try:
            # Get designer info
            user_row = conn.execute(
                "SELECT * FROM user_account WHERE user_id = ? AND role = 'interior_designer'", (designer_id,)
            ).fetchone()
            if not user_row:
                return None

            # Company info
            company_row = conn.execute(
                "SELECT * FROM company WHERE designer_id = ?", (designer_id,)
            ).fetchone()

            # Projects
            proj_rows = conn.execute(
                "SELECT project_id, title, status, created_at, updated_at FROM project WHERE designer_id = ? ORDER BY created_at DESC",
                (designer_id,)
            ).fetchall()
            projects = [dict(r) for r in proj_rows]

            # Reviews
            rev_rows = conn.execute(
                "SELECT review_id, rating, comment, status, submitted_at FROM customer_review WHERE designer_id = ? ORDER BY submitted_at DESC",
                (designer_id,)
            ).fetchall()
            reviews = [dict(r) for r in rev_rows]

            # Views over time (last 30 days)
            view_rows = conn.execute(
                """
                SELECT date(viewed_at) as view_date, COUNT(*) as count
                FROM project_view pv
                JOIN project p ON pv.project_id = p.project_id
                WHERE p.designer_id = ? AND viewed_at >= date('now', '-30 days')
                GROUP BY date(viewed_at)
                ORDER BY view_date
                """,
                (designer_id,)
            ).fetchall()
            views_over_time = [dict(r) for r in view_rows]

            # Shortlists over time (last 30 days)
            sl_rows = conn.execute(
                """
                SELECT date(event_at) as event_date, COUNT(*) as count
                FROM project_shortlist_event pse
                JOIN project p ON pse.project_id = p.project_id
                WHERE p.designer_id = ? AND pse.action = 'add' AND event_at >= date('now', '-30 days')
                GROUP BY date(event_at)
                ORDER BY event_date
                """,
                (designer_id,)
            ).fetchall()
            shortlists_over_time = [dict(r) for r in sl_rows]

            return {
                "designer": dict(user_row),
                "company": dict(company_row) if company_row else None,
                "projects": projects,
                "reviews": reviews,
                "views_over_time": views_over_time,
                "shortlists_over_time": shortlists_over_time,
            }
        except Exception as e:
            self.errors.append(f"Failed to load designer detail: {e}")
            return None


class PlatformSettingsController:
    def __init__(self):
        self.errors = []

    def get_settings(self):
        """Get current platform settings (from a simple key-value store in a settings table)."""
        conn = get_db()
        try:
            # Create settings table if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS platform_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

            rows = conn.execute("SELECT key, value, description FROM platform_settings").fetchall()
            settings = {r["key"]: {"value": r["value"], "description": r["description"]} for r in rows}
            return settings
        except Exception as e:
            self.errors.append(f"Failed to load settings: {e}")
            return {}

    def get_default_settings(self):
        """Return default settings structure."""
        return {
            "site_name": {"value": "IDEAL Platform", "description": "Platform display name"},
            "site_description": {"value": "Interior Design Project Platform", "description": "Platform tagline/description"},
            "max_projects_per_designer": {"value": "50", "description": "Maximum active projects per designer"},
            "enable_notifications": {"value": "true", "description": "Enable email notifications"},
            "notification_email": {"value": "admin@ideal.test", "description": "Default notification recipient"},
            "maintenance_mode": {"value": "false", "description": "Enable maintenance mode"},
            "allow_new_registrations": {"value": "true", "description": "Allow new user registrations"},
            "session_timeout_minutes": {"value": "60", "description": "Session timeout in minutes"},
        }

    def update_settings(self, form_data):
        """Update platform settings from form data."""
        conn = get_db()
        try:
            defaults = self.get_default_settings()
            updated = []

            for key, info in defaults.items():
                if key in form_data:
                    new_value = form_data[key].strip()
                    # For checkboxes, handle boolean
                    if key in ("enable_notifications", "maintenance_mode", "allow_new_registrations"):
                        new_value = "true" if form_data.get(key) else "false"

                    conn.execute(
                        """
                        INSERT INTO platform_settings (key, value, description, updated_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?
                        """,
                        (key, new_value, info["description"], now(), new_value, now())
                    )
                    updated.append(key)

            conn.commit()
            return updated
        except Exception as e:
            conn.rollback()
            self.errors.append(f"Failed to save settings: {e}")
            return []