# Task Approval Workflow API

A FastAPI service that manages approval workflows for different task types, built with clean layered architecture.

**Stack:** Python 3.13 · FastAPI · Pydantic v2 · UV · Docker

---

## Quick Start

```bash
# Install dependencies (creates .venv automatically)
uv sync

# Run the API
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest tests/ -v
```

Once running, open:

| URL | Description |
|---|---|
| http://127.0.0.1:8000/docs | Interactive Swagger UI — try endpoints in the browser |
| http://127.0.0.1:8000/redoc | ReDoc — alternative docs view |

---

## Docker

```bash
# Build the image
docker build -t task-approval-mgmt .

# Run the container
docker run -p 8000:8000 task-approval-mgmt
```

---

## Project Structure

```
app/
├── models/
│   └── task.py              # Domain entities + enums (TaskBase subclasses)
├── schemas/
│   ├── task.py              # API request DTOs + type-specific validation rules
│   └── responses.py         # API response schemas (separate from domain models)
├── repository/
│   ├── base.py              # TaskRepositoryProtocol — abstract interface
│   └── task_repository.py   # Async in-memory implementation
├── services/
│   └── task_service.py      # Business logic + status transitions
├── routers/
│   └── tasks.py             # Thin HTTP layer + dependency wiring
├── exceptions/
│   ├── __init__.py          # AppException base + re-exports
│   ├── task_exceptions.py   # TaskNotFound, TaskAlreadyProcessed
│   └── handlers.py          # Global exception handlers registered on app
├── middleware/
│   └── logging_middleware.py  # Request/response logging
└── main.py                  # FastAPI app entry point

tests/
└── test_tasks.py            # 7 async tests covering creation, approval flow, validation errors
```

---

## Architecture Decisions

### Layer Separation

The architecture follows a strict request flow:

```
HTTP Request → Router → Service → Repository
                  ↓                    ↓
             Schema (DTO)        Entity (domain model)
```

**Router** (`routers/tasks.py`) — pure HTTP wiring. Every endpoint is a one-liner that delegates to the service. No business logic, no conditionals.

**Service** (`services/task_service.py`) — owns all business rules: 404 on missing tasks, 409 on invalid status transitions, schema-to-entity mapping. The only layer that raises domain exceptions (`TaskNotFound`, `TaskAlreadyProcessed`), which the exception handlers translate to HTTP responses.

**Repository** (`repository/task_repository.py`) — owns storage. All methods are `async` so the interface is identical whether backed by a dict, PostgreSQL, or Redis. The service depends on `TaskRepositoryProtocol`, not the concrete class — swapping the backing store requires zero changes to the service or router.

### Models vs Schemas

| | `models/task.py` | `schemas/task.py` | `schemas/responses.py` |
|---|---|---|---|
| Purpose | Domain entities | API request DTOs | API response contract |
| Has `id`, `status`, timestamps | Yes | No | Yes |
| Has validation rules | No | Yes | No |
| Used by | Repository, Service | Router (request parsing) | Router (response serialisation) |

Separating request schemas, domain models, and response schemas means each can evolve independently. Internal fields added to a domain model never leak into the API response.

### Polymorphism via Discriminated Unions

Each task type is a distinct Pydantic model with a `type: Literal["..."]` field. Pydantic uses this as a discriminator to automatically select the correct model at parse time — no `if/elif` dispatch needed at the boundary.

```python
TaskCreateRequest = Annotated[
    Union[DataAccessTaskCreate, ResourceProvisionTaskCreate, ConfigChangeTaskCreate],
    Field(discriminator="type"),
]
```

Type-specific validation rules (e.g. `new_value != current_value` for `ConfigChangeTask`, `environment` regex for `ResourceProvisionTask`) live on their respective schema classes — not in shared logic.

### Repository Protocol (Dependency Inversion)

The service depends on `TaskRepositoryProtocol` — a `typing.Protocol` — not on the concrete `TaskRepository` class. This is the Dependency Inversion Principle: high-level business logic depends on an abstraction, not an implementation.

```python
class TaskRepositoryProtocol(Protocol):
    async def save(self, task: AnyTask) -> AnyTask: ...
    async def get_by_id(self, task_id: str) -> AnyTask | None: ...
    async def update_status(self, task_id: str, status: TaskStatus) -> AnyTask | None: ...
```

### Status Transitions

Only one valid transition path exists: `PENDING → APPROVED` or `PENDING → REJECTED`. The service enforces this with a single guard in `_transition()`. Attempting to approve or reject a non-PENDING task returns `409 Conflict`.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/tasks` | Create a new task (starts as `PENDING`) |
| `GET` | `/tasks/{id}` | Fetch a task by ID |
| `PATCH` | `/tasks/{id}/approve` | Approve a pending task |
| `PATCH` | `/tasks/{id}/reject` | Reject a pending task |

### Example Payloads

**DataAccessTask**
```json
{
  "type": "data_access",
  "dataset_name": "sales_db",
  "access_level": "READ",
  "justification": "Needed for quarterly report analysis"
}
```

**ResourceProvisionTask**
```json
{
  "type": "resource_provision",
  "resource_type": "VM",
  "quantity": 3,
  "environment": "staging"
}
```

**ConfigChangeTask**
```json
{
  "type": "config_change",
  "config_key": "MAX_CONNECTIONS",
  "current_value": "100",
  "new_value": "200"
}
```

---

## Testing

Tests use `httpx.AsyncClient` with `ASGITransport` and `pytest-asyncio` for true async testing.

> **Why not `TestClient`?** FastAPI's `TestClient` is a synchronous wrapper — it runs async routes in a thread but test functions remain sync. `AsyncClient` with `async def` tests hits the actual ASGI async code path end-to-end.

```bash
uv run pytest tests/ -v
```

---

## What Would Change for Production

This is an in-memory prototype, so here's what I'd change before putting it in front of real users.

### Persistence — PostgreSQL + SQLAlchemy

I'd swap the in-memory dict for PostgreSQL. SQLAlchemy 2.x with async support (`asyncpg` driver) fits naturally here — the repository interface is already fully async, so only `TaskRepository` changes. Alembic handles migrations.

```python
# Only this class changes — service and router stay identical
class PostgresTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, task: AnyTask) -> AnyTask:
        self._session.add(TaskORM.from_domain(task))
        await self._session.commit()
        return task
```

### Caching — Redis

For a read-heavy approval dashboard, I'd add Redis caching inside the repository: `get_by_id` checks the cache first, `update_status` invalidates it. Nothing above the repository layer needs to know caching exists.

I'd use `redis.asyncio` (part of the `redis-py` package) and cache serialised task JSON with a TTL of ~60 seconds. Approval/rejection would `DEL` the key immediately to avoid stale reads.

### Authentication — JWT via FastAPI dependency

I'd add a `get_current_user` dependency at the router level and inject the caller identity into the service. That keeps auth completely out of business logic.

```python
@router.patch("/{task_id}/approve")
async def approve_task(
    task_id: str,
    service: ServiceDep,
    current_user: User = Depends(get_current_user),  # JWT decoded here
) -> AnyTaskResponse:
    return to_response(await service.approve_task(task_id, approved_by=current_user.id))
```

For the token layer I'd use `python-jose` for JWT decode and `passlib` for password hashing. OAuth2 with Bearer tokens is the standard FastAPI pattern and works well with most identity providers.

### Observability

Structured JSON logs (via `structlog`), Prometheus metrics exposed at `/metrics`, and distributed tracing with OpenTelemetry. The logging middleware is already in place — it just needs to emit JSON instead of plain text so log aggregators like Datadog or Grafana Loki can parse fields properly.
