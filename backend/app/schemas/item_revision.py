"""
Pydantic schemas for item revision endpoints.
"""

from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any, Dict, List
from datetime import datetime


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class RevisionType(str, Enum):
    """Types of revisions."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    RESTORE = "RESTORE"


class ChangeDetail(BaseModel):
    """Represents a single field change."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    old: Optional[Any] = None
    new: Optional[Any] = None


class RelatedUser(BaseModel):
    """Minimal user info for embedding in revision response."""

    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )

    id: str
    name: str
    email: str

    @field_validator("id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Optional[str]:
        return str(v) if v else None


class ItemRevisionBase(BaseModel):
    """Base schema for item revisions."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    revision_number: int
    revision_type: RevisionType
    name: str
    sku: str
    description: Optional[str] = None
    quantity: int
    reorder_point: int
    unit_price: float
    status: str
    category_id: Optional[str] = None
    location_id: Optional[str] = None
    image_key: Optional[str] = None
    custom_attributes: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, ChangeDetail]] = None
    change_summary: Optional[str] = None


class ItemRevision(ItemRevisionBase):
    """Full item revision response schema."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    inventory_item_id: str
    created_by: Optional[str] = None
    creator: Optional[RelatedUser] = None
    created_at: datetime

    @field_validator(
        "id", "inventory_item_id", "created_by", "category_id", "location_id",
        mode="before"
    )
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Optional[str]:
        return str(v) if v else None


class ItemRevisionSummary(BaseModel):
    """Summarized revision for list views."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    revision_number: int
    revision_type: RevisionType
    change_summary: Optional[str] = None
    created_by: Optional[str] = None
    creator: Optional[RelatedUser] = None
    created_at: datetime

    @field_validator("id", "created_by", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v: Any) -> Optional[str]:
        return str(v) if v else None


class RevisionCompare(BaseModel):
    """Schema for comparing two revisions."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    from_revision: ItemRevision
    to_revision: ItemRevision
    differences: Dict[str, ChangeDetail]


class RestoreRevisionRequest(BaseModel):
    """Request schema for restoring an item to a previous revision."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    revision_number: int
    reason: Optional[str] = None
