from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.models.task import (
    AccessLevel,
    ConfigChangeTask,
    DataAccessTask,
    ResourceProvisionTask,
    ResourceType,
    TaskStatus,
)


class DataAccessTaskResponse(BaseModel):
    id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    type: Literal["data_access"]
    dataset_name: str
    access_level: AccessLevel
    justification: str

    @classmethod
    def from_domain(cls, task: DataAccessTask) -> DataAccessTaskResponse:
        return cls.model_validate(task.model_dump())


class ResourceProvisionTaskResponse(BaseModel):
    id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    type: Literal["resource_provision"]
    resource_type: ResourceType
    quantity: int
    environment: str

    @classmethod
    def from_domain(cls, task: ResourceProvisionTask) -> ResourceProvisionTaskResponse:
        return cls.model_validate(task.model_dump())


class ConfigChangeTaskResponse(BaseModel):
    id: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    type: Literal["config_change"]
    config_key: str
    current_value: str
    new_value: str

    @classmethod
    def from_domain(cls, task: ConfigChangeTask) -> ConfigChangeTaskResponse:
        return cls.model_validate(task.model_dump())


AnyTaskResponse = Annotated[
    DataAccessTaskResponse | ResourceProvisionTaskResponse | ConfigChangeTaskResponse,
    Field(discriminator="type"),
]


def to_response(
    task: DataAccessTask | ResourceProvisionTask | ConfigChangeTask,
) -> DataAccessTaskResponse | ResourceProvisionTaskResponse | ConfigChangeTaskResponse:
    """Map a domain entity to its corresponding response schema."""
    if isinstance(task, DataAccessTask):
        return DataAccessTaskResponse.from_domain(task)
    if isinstance(task, ResourceProvisionTask):
        return ResourceProvisionTaskResponse.from_domain(task)
    if isinstance(task, ConfigChangeTask):
        return ConfigChangeTaskResponse.from_domain(task)
    raise ValueError(f"Unknown task type: {type(task)}")
