import math
from typing import TypeVar, Generic, Sequence
from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class PageMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class Page(BaseModel, Generic[T]):
    data: Sequence[T]
    meta: PageMeta


async def paginate(
    session: AsyncSession,
    query: Select,
    page: int = 1,
    per_page: int = 20,
) -> tuple[Sequence, PageMeta]:
    per_page = min(per_page, 100)
    count_q = select(func.count()).select_from(query.subquery())
    total = (await session.execute(count_q)).scalar_one()
    rows = (
        await session.execute(query.offset((page - 1) * per_page).limit(per_page))
    ).scalars().all()
    meta = PageMeta(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=max(1, math.ceil(total / per_page)),
    )
    return rows, meta
