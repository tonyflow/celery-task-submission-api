import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock redis before any app imports
mock_redis = MagicMock()
sys.modules["redis"] = mock_redis
mock_redis_instance = MagicMock()
mock_redis_instance.hget.return_value = None  # No cached user
mock_redis.Redis.return_value = mock_redis_instance

from fastapi.testclient import TestClient

import auth
from api import app
from models import UserResponseBase, TaskResponseBase, TaskStateResponse, UserCreditsResponse


@pytest.fixture
def mock_admin_user():
    user = MagicMock()
    user.name = "admin"
    user.api_key = "admin-api-key"
    user.credits = 1000
    return user


@pytest.fixture
def mock_regular_user():
    user = MagicMock()
    user.name = "test_user"
    user.api_key = "test-api-key"
    user.credits = 500
    return user


@pytest.fixture
def client_with_admin(mock_admin_user):
    app.dependency_overrides[auth.get_current_user] = lambda: mock_admin_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_user(mock_regular_user):
    app.dependency_overrides[auth.get_current_user] = lambda: mock_regular_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestGetUsers:
    def test_get_users_returns_list(self, client):
        mock_users = [
            UserResponseBase(name="user1"),
            UserResponseBase(name="user2"),
        ]

        with patch("api.service.get_all_users", new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = mock_users

            response = client.get("/users")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "user1"
            assert data[1]["name"] == "user2"


class TestCreateAdditionTask:
    def test_create_task_success(self, client_with_user):
        with patch("api.service.create_addition_task", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = TaskResponseBase(task_id="task-123")

            response = client_with_user.post("/task?x=5&y=3", headers={"Authorization": "Bearer test-api-key"})

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "task-123"


class TestPollTaskState:
    def test_poll_pending_task(self, client):
        with patch("api.service.poll_task_state") as mock_poll:
            mock_poll.return_value = TaskStateResponse(task_id="task-123", state="PENDING")

            response = client.get("/poll/task-123")

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "task-123"
            assert data["state"] == "PENDING"
            assert data["result"] is None

    def test_poll_completed_task(self, client):
        with patch("api.service.poll_task_state") as mock_poll:
            mock_poll.return_value = TaskStateResponse(task_id="task-123", state="SUCCESS", result=8)

            response = client.get("/poll/task-123")

            assert response.status_code == 200
            data = response.json()
            assert data["task_id"] == "task-123"
            assert data["state"] == "SUCCESS"
            assert data["result"] == 8


class TestGetUserCredits:
    def test_get_credits_as_admin(self, client_with_admin):
        with patch("api.service.get_user_credits", new_callable=AsyncMock) as mock_get_credits:
            mock_get_credits.return_value = UserCreditsResponse(name="test_user", credits=500)

            response = client_with_admin.get("/credits/test_user", headers={"Authorization": "Bearer admin-api-key"})

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "test_user"
            assert data["credits"] == 500


class TestUpdateUserCredits:
    def test_update_credits_as_admin(self, client_with_admin):
        with patch("api.service.update_user_credits", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = UserCreditsResponse(name="test_user", credits=600)

            response = client_with_admin.put(
                "/credits/test_user?api_credits=100",
                headers={"Authorization": "Bearer admin-api-key"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "test_user"
            assert data["credits"] == 600
            mock_update.assert_called_once_with("test_user", 100)
