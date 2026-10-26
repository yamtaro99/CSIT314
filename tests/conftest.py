import io
import os
import sys

import pytest
from werkzeug.datastructures import FileStorage

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.db import init_db
from app.entity.category import Category
from app.entity.user_account import UserAccount

PASSWORD = "Test-Password-1"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
        "DATABASE": str(tmp_path / "test.sqlite"),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
    })
    with app.app_context():
        init_db()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


def make_user(role, email=None, status="active", name="Test User"):
    account = UserAccount(email=email or f"{role}@test.local", name=name, role=role, status=status)
    account.set_password(PASSWORD)
    assert account.create()
    return account


@pytest.fixture
def designer(app):
    return make_user(UserAccount.INTERIOR_DESIGNER, "designer@test.local", name="Dana Designer")


@pytest.fixture
def other_designer(app):
    return make_user(UserAccount.INTERIOR_DESIGNER, "other@test.local", name="Olly Other")


@pytest.fixture
def categories(app):
    result = []
    for name in ("Modern", "Scandinavian", "Industrial"):
        c = Category(name=name)
        c.create()
        result.append(c)
    return result


def login(client, email, password=PASSWORD):
    return client.post("/login", data={"email": email, "password": password})


def upload(name, data):
    return FileStorage(stream=io.BytesIO(data), filename=name)
