from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.models.task import TaskStatus
from app.repository.task_repository import AnyTask


@runtime_checkable
class TaskRepositoryProtocol(Protocol):
    """Abstract interface for task storage.

    The service depends on this protocol, not on any concrete implementation.
    Swapping in-memory storage for PostgreSQL, Redis, etc. only requires
    a new class that satisfies this interface — the service never changes.
    """

    async def save(self, task: AnyTask) -> AnyTask: ...

    async def get_by_id(self, task_id: str) -> AnyTask | None: ...

    async def update_status(self, task_id: str, status: TaskStatus) -> AnyTask | None: ...
