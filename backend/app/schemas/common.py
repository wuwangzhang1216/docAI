"""Common schemas used across the application."""

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema."""

    items: List[T]
    total: int
    limit: int
    offset: int
    has_more: bool

    class Config:
        from_attributes = True
