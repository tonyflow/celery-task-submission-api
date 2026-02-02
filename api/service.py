import logging

from fastapi import HTTPException
from sqlalchemy import select, update, insert

from celery_app import instance as celery_instance
from database.engine import async_session
from database.models import User, UserTaskHistory
from models import TaskResponseBase, TaskStateResponse, UserCreditsResponse

_logger = logging.getLogger(__name__)

API_COST = 10
"""Arbitrary API cost for each task submitted."""


async def get_all_users() -> list[User]:
    """Retrieve all users' names."""
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()


async def create_addition_task(user: User, x: int, y: int) -> TaskResponseBase:
    """Create addition task.

    Args:
        user (User): User triggering the task.
        x (int): First operand.
        y (int): Second operand.

    Returns:
        TaskResponseBase: Task response including the spawned task ID.
    """
    if user.credits - API_COST < 0:
        raise HTTPException(status_code=403, detail="Insufficient credits")

    # 1. Submit the task
    task = celery_instance.send_task("worker.add", args=[x, y])

    # 2. Deduct user credits upon submission.
    # For a fairer credit deduction implementation check the /fair_poll endpoint
    async with async_session() as session:
        # 3. Trace task history for user
        await session.execute(insert(UserTaskHistory).values(user_name=user.name, task_id=task.id, cost=API_COST))

        # 4. Deduct user credits
        await session.execute(update(User).where(User.name == user.name).values(credits=User.credits - API_COST))

        # Commit changes
        await session.commit()

    return TaskResponseBase(task_id=task.id)


def poll_task_state(task_id: str) -> TaskStateResponse:
    """Poll task state.

    Args:
        task_id (str): Celery Task ID.

    Returns:
        TaskStateResponse: The json includes the task ID itself, the state (SUCCESS, PENDING...)
        and if the task has completed successfully, the result will be part of the response.
    """
    result = celery_instance.AsyncResult(task_id)
    response = TaskStateResponse(task_id=task_id, state=result.state)
    if result.ready():
        response.result = result.result

    return response


async def fair_poll_task_state(user: User, task_id: str) -> TaskResponseBase:
    """(Fair) Poll task state.

    The difference with the regular poll_task_state is that this function will only update the
    user's credits if the task has completed successfully. If this is to be used, the credit
    deduction should be removed from the create_addition_task function.

    Args:
        user (User): User triggering the task.
        task_id (str): Celery Task ID.

    Returns:
        TaskStateResponse: The json includes the task ID itself, the state (SUCCESS, PENDING...)
        and if the task has completed successfully, the result will be part of the response.
    """
    task_state_response = poll_task_state(task_id)

    # 1. Make sure that the task has been completed and a result has been computed and only then,
    if task_state_response.state is not None and task_state_response.state == "SUCCESS" and task_state_response.result is not None:
        # 2. Update user credits
        async with async_session() as session:
            user_task_result = await session.execute(select(UserTaskHistory).where(user_name=user.name, task_id=task_id))
            user_task_trace = user_task_result.scalar_one_or_none()
            if user_task_trace is not None:
                await session.execute(update(User).where(User.name == user.name).values(credits=user.credits - user_task_trace.cost))
            else:
                _logger.error(f"No user task found for task {task_id}")

            # Commit changes
            await session.commit()
    return task_state_response


async def get_user_credits(user_name: str) -> UserCreditsResponse:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.name == user_name))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        return UserCreditsResponse(name=user.name, credits=user.credits)


async def update_user_credits(user_name: str, additional_user_credits: int) -> UserCreditsResponse:
    async with async_session() as session:
        result = await session.execute(
            update(User).where(User.name == user_name)
            .values(credits=User.credits + additional_user_credits)
            .returning(User.name, User.credits)
        )

        affected_user = result.fetchone()

        if affected_user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        await session.commit()

        return UserCreditsResponse(name=affected_user.name, credits=affected_user.credits)
