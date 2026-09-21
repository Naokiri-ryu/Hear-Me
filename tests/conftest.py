import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Strong dummy keys for the whole test session so PyJWT/Fernet never emit
# InsecureKeyLengthWarning and tests never depend on a real .env key. Must be
# set BEFORE importing api.* so the Settings singleton (and the module-level
# Fernet instance) are built with them.
TEST_SECRET_KEY = "test-secret-key-00000000000000000000000000-secret"
TEST_TOKEN_ENCRYPTION_KEY = "test-token-encryption-key-0000000000000000000000"

os.environ.setdefault("SECRET_KEY", TEST_SECRET_KEY)
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", TEST_TOKEN_ENCRYPTION_KEY)

from api.db import get_db  # noqa: E402
from api.main import app  # noqa: E402
from api.security import hash_password  # noqa: E402
from models import Base  # noqa: E402
from models.user import User  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def secure_test_keys():
    """Pin >=32-byte SECRET_KEY/TOKEN_ENCRYPTION_KEY for the test session."""
    from api.config import settings

    settings.SECRET_KEY = TEST_SECRET_KEY
    settings.TOKEN_ENCRYPTION_KEY = TEST_TOKEN_ENCRYPTION_KEY
    yield


@pytest.fixture
def dbfactory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    yield factory
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(dbfactory):
    with dbfactory() as session:
        yield session


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user(db_session):
    row = User(
        email="user@example.com",
        password_hash=hash_password("password123"),
        display_name="Tester",
    )
    db_session.add(row)
    db_session.commit()
    db_session.refresh(row)
    return row


@pytest.fixture
def token(client):
    resp = client.post(
        "/auth/register",
        json={"email": "u@example.com", "password": "password123", "display_name": "Tester"},
    )
    assert resp.status_code == 201, resp.text
    resp = client.post(
        "/auth/login",
        json={"email": "u@example.com", "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def eager():
    from workers.celery_app import celery_app

    previous = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = previous