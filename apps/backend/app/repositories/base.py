from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.errors import NotFound
from ..db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


def coerce_uuid(value: uuid.UUID | str) -> uuid.UUID | str:
    """Coerce a UUID string (e.g. from a URL path) into a ``uuid.UUID``.

    SQLAlchemy's ``Uuid`` column type expects a real UUID when binding a value;
    a bare string raises ``'str' object has no attribute 'hex'``. Non-UUID strings
    (e.g. ``Setting`` keys) are returned unchanged.
    """
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return value
    return value


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, entity_id: uuid.UUID | str) -> ModelT | None:
        return await self.session.get(self.model, coerce_uuid(entity_id))

    async def get_or_404(self, entity_id: uuid.UUID | str) -> ModelT:
        obj = await self.get(entity_id)
        if obj is None:
            raise NotFound(f"{self.model.__name__} не найден.")
        return obj

    async def list_all(self) -> list[ModelT]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())

    def add(self, obj: ModelT) -> ModelT:
        self.session.add(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        await self.session.delete(obj)

    async def flush(self) -> None:
        await self.session.flush()
