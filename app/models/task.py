from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AccessLevel(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    ADMIN = "ADMIN"


class ResourceType(str, Enum):
    VM = "VM"
    DATABASE = "DATABASE"
    STORAGE = "STORAGE"


class TaskBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DataAccessTask(TaskBase):
    type: Literal["data_access"]
    dataset_name: str
    access_level: AccessLevel
    justification: str


class ResourceProvisionTask(TaskBase):
    type: Literal["resource_provision"]
    resource_type: ResourceType
    quantity: int
    environment: str


class ConfigChangeTask(TaskBase):
    type: Literal["config_change"]
    config_key: str
    current_value: str
    new_value: str


Task = Annotated[
    DataAccessTask | ResourceProvisionTask | ConfigChangeTask,
    Field(discriminator="type"),
]
