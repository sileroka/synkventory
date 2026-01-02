from datetime import datetime
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
import uuid

T = TypeVar("T")


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class ResponseMeta(BaseModel):
    """Metadata for all API responses."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class PaginationMeta(ResponseMeta):
    """Metadata for paginated responses."""

    page: int
    page_size: int
    total_items: int
    total_pages: int


class DataResponse(BaseModel, Generic[T]):
    """Standard response wrapper for single items."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data: T
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ListResponse(BaseModel, Generic[T]):
    """Standard response wrapper for collections with pagination."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    data: list[T]
    meta: PaginationMeta


class ErrorDetail(BaseModel):
    """Error details structure."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Standard error response format."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    error: ErrorDetail
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class MessageResponse(BaseModel):
    """Simple message response."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    message: str
    meta: ResponseMeta = Field(default_factory=ResponseMeta)
