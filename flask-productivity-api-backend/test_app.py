"""Basic test suite for the Productivity API."""
import pytest
from server.app import create_app, db
from server.models import User, Task


@pytest.fixture
def app():
    """Create application configured for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def auth_client(client):
    """Client with an authenticated session."""
    # Register
    client.post("/signup", json={"username": "tester", "password": "testpass"})
    return client


class TestAuth:
    """Authentication endpoint tests."""

    def test_signup_creates_user(self, client):
        resp = client.post("/signup", json={"username": "alice", "password": "secret"})
        assert resp.status_code == 201
        assert resp.get_json()["username"] == "alice"

    def test_signup_duplicate_username(self, client):
        client.post("/signup", json={"username": "alice", "password": "secret"})
        resp = client.post("/signup", json={"username": "alice", "password": "other"})
        assert resp.status_code == 409

    def test_login_success(self, client):
        client.post("/signup", json={"username": "bob", "password": "pass"})
        resp = client.post("/login", json={"username": "bob", "password": "pass"})
        assert resp.status_code == 200
        assert resp.get_json()["username"] == "bob"

    def test_login_failure(self, client):
        resp = client.post("/login", json={"username": "nobody", "password": "wrong"})
        assert resp.status_code == 401

    def test_check_session_when_logged_in(self, auth_client):
        resp = auth_client.get("/check_session")
        assert resp.status_code == 200
        assert resp.get_json()["username"] == "tester"

    def test_check_session_when_logged_out(self, client):
        resp = client.get("/check_session")
        assert resp.status_code == 401

    def test_logout(self, auth_client):
        resp = auth_client.delete("/logout")
        assert resp.status_code == 204


class TestTaskCRUD:
    """Task CRUD operation tests."""

    def test_create_task(self, auth_client):
        resp = auth_client.post("/tasks", json={
            "title": "Write tests",
            "description": "Cover all endpoints",
            "priority": "high"
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["title"] == "Write tests"
        assert data["priority"] == "high"

    def test_list_tasks_paginated(self, auth_client):
        auth_client.post("/tasks", json={"title": "Task 1"})
        auth_client.post("/tasks", json={"title": "Task 2"})
        resp = auth_client.get("/tasks?page=1&per_page=5")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "tasks" in data
        assert "pagination" in data

    def test_get_single_task(self, auth_client):
        create_resp = auth_client.post("/tasks", json={"title": "Read docs"})
        task_id = create_resp.get_json()["id"]
        resp = auth_client.get(f"/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "Read docs"

    def test_update_task(self, auth_client):
        create_resp = auth_client.post("/tasks", json={"title": "Old title"})
        task_id = create_resp.get_json()["id"]
        resp = auth_client.patch(f"/tasks/{task_id}", json={"title": "New title"})
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "New title"

    def test_delete_task(self, auth_client):
        create_resp = auth_client.post("/tasks", json={"title": "Delete me"})
        task_id = create_resp.get_json()["id"]
        resp = auth_client.delete(f"/tasks/{task_id}")
        assert resp.status_code == 200

    def test_unauthorized_access(self, client):
        resp = client.get("/tasks")
        assert resp.status_code == 401

    def test_cannot_access_other_users_task(self, app):
        with app.test_client() as alice:
            alice.post("/signup", json={"username": "alice", "password": "pass"})
            task = alice.post("/tasks", json={"title": "Alice secret"})
            task_id = task.get_json()["id"]

        with app.test_client() as bob:
            bob.post("/signup", json={"username": "bob", "password": "pass"})
            resp = bob.get(f"/tasks/{task_id}")
            assert resp.status_code == 404
