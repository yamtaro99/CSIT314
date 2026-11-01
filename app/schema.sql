PRAGMA foreign_keys = OFF;
DROP TABLE IF EXISTS project_category;
DROP TABLE IF EXISTS project_photo;
DROP TABLE IF EXISTS project;
DROP TABLE IF EXISTS category;
DROP TABLE IF EXISTS user_account;
DROP TABLE IF EXISTS company;

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
    registration_no TEXT    NOT NULL,
    address         TEXT    NOT NULL DEFAULT '',
    phone           TEXT    NOT NULL DEFAULT '',
    description     TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL
);

-- Customer Project Interaction

-- Project Interest Tracking
