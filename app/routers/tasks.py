from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.repository.task_repository import TaskRepository
from app.schemas.responses import AnyTaskResponse, to_response
from app.schemas.task import TaskCreateRequest
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])

# ---------------------------------------------------------------------------
# Dependency wiring
# ---------------------------------------------------------------------------

_repository = TaskRepository()


def get_repository() -> TaskRepository:
    return _repository


def get_service(
    repo: Annotated[TaskRepository, Depends(get_repository)],
) -> TaskService:
    return TaskService(repo)


ServiceDep = Annotated[TaskService, Depends(get_service)]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AnyTaskResponse)
async def create_task(payload: TaskCreateRequest, service: ServiceDep) -> AnyTaskResponse:
    return to_response(await service.create_task(payload))


@router.get("/{task_id}", response_model=AnyTaskResponse)
async def get_task(task_id: str, service: ServiceDep) -> AnyTaskResponse:
    return to_response(await service.get_task(task_id))


@router.patch("/{task_id}/approve", response_model=AnyTaskResponse)
async def approve_task(task_id: str, service: ServiceDep) -> AnyTaskResponse:
    return to_response(await service.approve_task(task_id))


@router.patch("/{task_id}/reject", response_model=AnyTaskResponse)
async def reject_task(task_id: str, service: ServiceDep) -> AnyTaskResponse:
    return to_response(await service.reject_task(task_id))
