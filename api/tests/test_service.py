import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from database.models import User
from service import (
    get_all_users,
    create_addition_task,
    poll_task_state,
    get_user_credits,
    update_user_credits,
    API_COST,
)


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.name = "test_user"
    user.api_key = "test-api-key"
    user.credits = 500
    return user


@pytest.mark.anyio
async def test_get_all_users():
    mock_user = MagicMock()
    mock_user.name = "test_user"

    with patch("service.async_session") as mock_session:
        mock_ctx = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_user]
        mock_ctx.execute = AsyncMock(return_value=mock_result)
        mock_session.return_value.__aenter__.return_value = mock_ctx

        result = await get_all_users()

        assert len(result) == 1
        assert result[0].name == "test_user"


@pytest.mark.anyio
async def test_create_addition_task_success(mock_user):
    with patch("service.celery_instance") as mock_celery, \
         patch("service.async_session") as mock_session:
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_celery.send_task.return_value = mock_task

        mock_ctx = AsyncMock()
        mock_ctx.execute = AsyncMock()
        mock_ctx.commit = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        result = await create_addition_task(mock_user, 5, 3)

        assert result.task_id == "task-123"
        mock_celery.send_task.assert_called_once_with("worker.add", args=[5, 3])


@pytest.mark.anyio
async def test_create_addition_task_insufficient_credits(mock_user):
    mock_user.credits = 5  # Less than API_COST

    with pytest.raises(HTTPException) as exc_info:
        await create_addition_task(mock_user, 5, 3)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient credits"


def test_poll_task_state_pending():
    with patch("service.celery_instance") as mock_celery:
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_result.ready.return_value = False
        mock_celery.AsyncResult.return_value = mock_result

        result = poll_task_state("task-123")

        assert result.task_id == "task-123"
        assert result.state == "PENDING"
        assert result.result is None


def test_poll_task_state_success():
    with patch("service.celery_instance") as mock_celery:
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.ready.return_value = True
        mock_result.result = 8
        mock_celery.AsyncResult.return_value = mock_result

        result = poll_task_state("task-123")

        assert result.task_id == "task-123"
        assert result.state == "SUCCESS"
        assert result.result == 8


@pytest.mark.anyio
async def test_get_user_credits_found():
    mock_user = MagicMock()
    mock_user.name = "test_user"
    mock_user.credits = 500

    with patch("service.async_session") as mock_session:
        mock_ctx = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_ctx.execute = AsyncMock(return_value=mock_result)
        mock_ctx.commit = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        result = await get_user_credits("test_user")

        assert result.name == "test_user"
        assert result.credits == 500


@pytest.mark.anyio
async def test_get_user_credits_not_found():
    with patch("service.async_session") as mock_session:
        mock_ctx = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_ctx.execute = AsyncMock(return_value=mock_result)
        mock_session.return_value.__aenter__.return_value = mock_ctx

        with pytest.raises(HTTPException) as exc_info:
            await get_user_credits("nonexistent")

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found."


@pytest.mark.anyio
async def test_update_user_credits_success():
    with patch("service.async_session") as mock_session:
        mock_ctx = AsyncMock()
        mock_row = MagicMock()
        mock_row.name = "test_user"
        mock_row.credits = 600
        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_ctx.execute = AsyncMock(return_value=mock_result)
        mock_ctx.commit = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        result = await update_user_credits("test_user", 100)

        assert result.name == "test_user"
        assert result.credits == 600


@pytest.mark.anyio
async def test_update_user_credits_user_not_found():
    with patch("service.async_session") as mock_session:
        mock_ctx = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_ctx.execute = AsyncMock(return_value=mock_result)
        mock_session.return_value.__aenter__.return_value = mock_ctx

        with pytest.raises(HTTPException) as exc_info:
            await update_user_credits("nonexistent", 100)

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "User not found."
