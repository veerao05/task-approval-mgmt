from __future__ import annotations

from datetime import UTC, datetime

from app.models.task import (
    ConfigChangeTask,
    DataAccessTask,
    ResourceProvisionTask,
    TaskStatus,
)

AnyTask = DataAccessTask | ResourceProvisionTask | ConfigChangeTask


class TaskRepository:
    """In-memory async repository.

    All methods are async so the interface is production-ready —
    swapping to a real DB only requires changing this class.
    """

    def __init__(self) -> None:
        self._store: dict[str, AnyTask] = {}

    async def save(self, task: AnyTask) -> AnyTask:
        self._store[task.id] = task
        return task

    async def get_by_id(self, task_id: str) -> AnyTask | None:
        return self._store.get(task_id)

    async def update_status(self, task_id: str, status: TaskStatus) -> AnyTask | None:
        task = self._store.get(task_id)
        if task is None:
            return None
        updated = task.model_copy(update={"status": status, "updated_at": datetime.now(UTC)})
        self._store[task_id] = updated
        return updated
