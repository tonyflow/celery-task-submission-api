import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from api import app, get_current_user
from database.models import User


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.name = "test_user"
    user.api_key = "test-api-key"
    user.credits = 500
    return user


@pytest.fixture
def mock_admin_user():
    user = MagicMock(spec=User)
    user.name = "admin"
    user.api_key = "admin-api-key"
    user.credits = 1000
    return user


@pytest.mark.anyio
async def test_get_users():
    mock_user = MagicMock()
    mock_user.name = "test_user"

    with patch("api.async_session") as mock_session:
        mock_ctx = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]
        mock_ctx.execute = AsyncMock(return_value=mock_result)
        mock_session.return_value.__aenter__.return_value = mock_ctx

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/users")

        assert response.status_code == 200
        assert response.json() == [{"name": "test_user"}]


@pytest.mark.anyio
async def test_create_task_success(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user

    with patch("api.celery_app") as mock_celery, \
         patch("api.async_session") as mock_session:
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_celery.send_task.return_value = mock_task
        mock_session.return_value.__aenter__.return_value = AsyncMock()

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/task?x=5&y=3")

        assert response.status_code == 200
        assert response.json() == {"task_id": "task-123"}

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_create_task_insufficient_credits(mock_user):
    mock_user.credits = 5
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/task?x=5&y=3")

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient credits"

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_poll_task_completed():
    with patch("api.celery_app") as mock_celery:
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.result = 8
        mock_celery.AsyncResult.return_value = mock_result

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/poll?task_id=task-123")

        assert response.status_code == 200
        assert response.json()["state"] == "SUCCESS"
        assert response.json()["result"] == 8


@pytest.mark.anyio
async def test_update_credits_non_admin_forbidden(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put("/credits/someone?api_credits=999")

    assert response.status_code == 403
    assert response.json()["detail"] == "Only admin users can update credits."

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_update_credits_as_admin(mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    with patch("api.async_session") as mock_session:
        mock_ctx = AsyncMock()
        mock_row = MagicMock()
        mock_row.name = "test_user"
        mock_row.credits = 999
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_ctx.execute = AsyncMock(return_value=mock_result)
        mock_ctx.commit = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put("/credits/test_user?api_credits=999")

        assert response.status_code == 200
        assert response.json() == {"name": "test_user", "credits": 999}

    app.dependency_overrides.clear()
