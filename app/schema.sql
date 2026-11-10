PRAGMA foreign_keys = OFF;
-- US03 / US07: Drop dependent interest tables before shared project/user tables.
DROP TABLE IF EXISTS project_shortlist_event;
DROP TABLE IF EXISTS project_shortlist;
DROP TABLE IF EXISTS project_view;
DROP TABLE IF EXISTS project_category;
DROP TABLE IF EXISTS project_photo;
DROP TABLE IF EXISTS project;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS user_account;
DROP TABLE IF EXISTS company;
DROP TABLE IF EXISTS consultation_slot;
DROP TABLE IF EXISTS customer_review;

PRAGMA foreign_keys = ON;

-- User Admin
CREATE TABLE user_account (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    role          TEXT    NOT NULL
                  CHECK (role IN ('user_admin', 'interior_designer', 'customer', 'platform_manager')),
    status        TEXT    NOT NULL DEFAULT 'active'
                  CHECK (status IN ('pending', 'active', 'suspended', 'deactivated')),
    created_at    TEXT    NOT NULL
);

-- Platform Management
CREATE TABLE category (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL
);

-- ID Portfolio Management
CREATE TABLE project (
    project_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    designer_id     INTEGER NOT NULL REFERENCES user_account (user_id),
    title           TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    location        TEXT    NOT NULL,
    completion_date TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'removed')),
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL
);
CREATE INDEX idx_project_designer ON project (designer_id);

CREATE TABLE project_photo (
    photo_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES project (project_id),
    file_url    TEXT    NOT NULL,
    caption     TEXT    NOT NULL DEFAULT '',
    uploaded_at TEXT    NOT NULL
);

CREATE TABLE project_category (
    project_id  INTEGER NOT NULL REFERENCES project (project_id),
    category_id INTEGER NOT NULL REFERENCES category (category_id),
    PRIMARY KEY (project_id, category_id)
);

-- ID Company Information
CREATE TABLE company (
    company_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    designer_id     INTEGER NOT NULL UNIQUE REFERENCES user_account (user_id),
    registration_no TEXT    NOT NULL UNIQUE,
    address         TEXT    NOT NULL DEFAULT '',
    phone           TEXT    NOT NULL DEFAULT '',
    description     TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE consultation_slot (
    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    designer_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_booked INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (designer_id) REFERENCES user_account (user_id)
);

CREATE TABLE customer_review (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    designer_id INTEGER NOT NULL,
    customer_id INTEGER,
    rating INTEGER NOT NULL,
    comment TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    submitted_at TEXT NOT NULL,
    FOREIGN KEY (designer_id) REFERENCES user_account (user_id)
);

-- Customer Project Interaction

-- Project Interest Tracking (US03 / US07)
-- Current favourites are independent of historical shortlist events.
CREATE TABLE project_shortlist (
    customer_id INTEGER NOT NULL REFERENCES user_account(user_id),
    project_id INTEGER NOT NULL REFERENCES project(project_id),
    created_at TEXT NOT NULL,
    PRIMARY KEY (customer_id, project_id)
);
CREATE INDEX idx_shortlist_project ON project_shortlist(project_id);

CREATE TABLE project_view (
    view_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES user_account(user_id),
    project_id INTEGER NOT NULL REFERENCES project(project_id),
    viewed_at TEXT NOT NULL,
    demo_event_key TEXT UNIQUE
);
CREATE INDEX idx_project_view_project ON project_view(project_id);

CREATE TABLE project_shortlist_event (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES user_account(user_id),
    project_id INTEGER NOT NULL REFERENCES project(project_id),
    action TEXT NOT NULL CHECK(action IN ('add', 'remove')),
    event_at TEXT NOT NULL,
    demo_event_key TEXT UNIQUE
);
CREATE INDEX idx_shortlist_event_project_time
    ON project_shortlist_event(project_id, event_at);
