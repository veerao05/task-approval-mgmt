from __future__ import annotations

import logging

from app.exceptions import TaskAlreadyProcessed, TaskNotFound
from app.models.task import (
    ConfigChangeTask,
    DataAccessTask,
    ResourceProvisionTask,
    TaskStatus,
)
from app.repository.base import TaskRepositoryProtocol
from app.repository.task_repository import AnyTask
from app.schemas.task import (
    ConfigChangeTaskCreate,
    DataAccessTaskCreate,
    ResourceProvisionTaskCreate,
)

logger = logging.getLogger(__name__)

AnyTaskCreate = DataAccessTaskCreate | ResourceProvisionTaskCreate | ConfigChangeTaskCreate


class TaskService:
    def __init__(self, repository: TaskRepositoryProtocol) -> None:
        self._repo = repository

    async def create_task(self, payload: AnyTaskCreate) -> AnyTask:
        """Build a domain entity from the validated DTO and persist it."""
        task = self._build_entity(payload)
        await self._repo.save(task)
        logger.info("Task created: id=%s type=%s", task.id, task.type)
        return task

    async def get_task(self, task_id: str) -> AnyTask:
        """Return a task by ID or raise TaskNotFound."""
        task = await self._repo.get_by_id(task_id)
        if task is None:
            logger.warning("Task not found: id=%s", task_id)
            raise TaskNotFound(task_id)
        return task

    async def approve_task(self, task_id: str) -> AnyTask:
        """Transition a PENDING task to APPROVED."""
        return await self._transition(task_id, TaskStatus.APPROVED)

    async def reject_task(self, task_id: str) -> AnyTask:
        """Transition a PENDING task to REJECTED."""
        return await self._transition(task_id, TaskStatus.REJECTED)

    async def _transition(self, task_id: str, new_status: TaskStatus) -> AnyTask:
        """Shared guard for approve/reject — only PENDING tasks may transition."""
        task = await self.get_task(task_id)

        if task.status != TaskStatus.PENDING:
            logger.warning(
                "Invalid transition attempt: id=%s current_status=%s target_status=%s",
                task_id,
                task.status.value,
                new_status.value,
            )
            raise TaskAlreadyProcessed(task_id, task.status.value)

        updated = await self._repo.update_status(task_id, new_status)
        assert updated is not None, "Task disappeared between get and update"
        logger.info("Task status updated: id=%s status=%s", task_id, new_status.value)
        return updated

    @staticmethod
    def _build_entity(payload: AnyTaskCreate) -> AnyTask:
        """Map a validated schema DTO → domain entity."""
        if isinstance(payload, DataAccessTaskCreate):
            return DataAccessTask(**payload.model_dump())
        if isinstance(payload, ResourceProvisionTaskCreate):
            return ResourceProvisionTask(**payload.model_dump())
        if isinstance(payload, ConfigChangeTaskCreate):
            return ConfigChangeTask(**payload.model_dump())
        raise ValueError(f"Unknown task type: {type(payload)}")
