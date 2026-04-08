from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from app.models.task import AccessLevel, ResourceType


class DataAccessTaskCreate(BaseModel):
    type: Literal["data_access"]
    dataset_name: str = Field(..., min_length=1)
    access_level: AccessLevel
    justification: str = Field(..., min_length=10)


class ResourceProvisionTaskCreate(BaseModel):
    type: Literal["resource_provision"]
    resource_type: ResourceType
    quantity: int = Field(..., gt=0, le=100)
    environment: str = Field(..., pattern=r"^(dev|staging|prod)$")


class ConfigChangeTaskCreate(BaseModel):
    type: Literal["config_change"]
    config_key: str = Field(..., min_length=1)
    current_value: str
    new_value: str

    @field_validator("new_value")
    @classmethod
    def new_value_must_differ(cls, v: str, info: ValidationInfo) -> str:
        if v == info.data.get("current_value"):
            raise ValueError("new_value must differ from current_value")
        return v


TaskCreateRequest = Annotated[
    DataAccessTaskCreate | ResourceProvisionTaskCreate | ConfigChangeTaskCreate,
    Field(discriminator="type"),
]
