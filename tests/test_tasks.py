import uuid
from collections.abc import AsyncGenerator

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.repository.task_repository import TaskRepository
from app.routers.tasks import get_repository


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Fresh in-memory store per test — no shared state between tests."""
    fresh_repo = TaskRepository()
    app.dependency_overrides[get_repository] = lambda: fresh_repo
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def create_task(client: AsyncClient, payload: dict[str, object]) -> dict[str, object]:
    """POST /tasks and assert 201."""
    response = await client.post("/tasks", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    result: dict[str, object] = response.json()
    return result


async def test_create_data_access_task(client: AsyncClient) -> None:
    """Creating a DataAccessTask returns the full entity with status PENDING."""
    payload: dict[str, object] = {
        "type": "data_access",
        "dataset_name": "sales_db",
        "access_level": "READ",
        "justification": "Needed for quarterly report analysis",
    }
    data = await create_task(client, payload)

    assert data["type"] == "data_access"
    assert data["dataset_name"] == "sales_db"
    assert data["status"] == "PENDING"
    assert "id" in data


async def test_approve_task(client: AsyncClient) -> None:
    """Approving a PENDING task transitions its status to APPROVED."""
    task = await create_task(
        client,
        {
            "type": "resource_provision",
            "resource_type": "VM",
            "quantity": 3,
            "environment": "staging",
        },
    )
    task_id = task["id"]

    response = await client.patch(f"/tasks/{task_id}/approve")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "APPROVED"


async def test_reject_task(client: AsyncClient) -> None:
    """Rejecting a PENDING task transitions its status to REJECTED."""
    task = await create_task(
        client,
        {
            "type": "config_change",
            "config_key": "MAX_CONNECTIONS",
            "current_value": "100",
            "new_value": "200",
        },
    )
    task_id = task["id"]

    response = await client.patch(f"/tasks/{task_id}/reject")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "REJECTED"


async def test_double_transition_conflict(client: AsyncClient) -> None:
    """Attempting to reject an already-approved task returns 409 Conflict."""
    task = await create_task(
        client,
        {
            "type": "data_access",
            "dataset_name": "hr_data",
            "access_level": "WRITE",
            "justification": "Updating employee records for audit",
        },
    )
    task_id = task["id"]

    await client.patch(f"/tasks/{task_id}/approve")

    response = await client.patch(f"/tasks/{task_id}/reject")
    assert response.status_code == status.HTTP_409_CONFLICT
    assert "PENDING" in response.json()["message"]


async def test_config_change_same_value_rejected(client: AsyncClient) -> None:
    """ConfigChangeTask fails validation when new_value equals current_value."""
    response = await client.post(
        "/tasks",
        json={
            "type": "config_change",
            "config_key": "TIMEOUT",
            "current_value": "30",
            "new_value": "30",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_resource_provision_invalid_environment(client: AsyncClient) -> None:
    """ResourceProvisionTask fails validation when environment is not dev/staging/prod."""
    response = await client.post(
        "/tasks",
        json={
            "type": "resource_provision",
            "resource_type": "DATABASE",
            "quantity": 1,
            "environment": "production",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_get_nonexistent_task_returns_404(client: AsyncClient) -> None:
    """Fetching a task that does not exist returns 404 Not Found."""
    task_id = str(uuid.uuid4())
    response = await client.get(f"/tasks/{task_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
