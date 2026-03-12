import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.custom_schema import CustomSchema
from app.shared.errors import NotFoundError
from app.shared.pagination import paginate


async def create_schema(db: AsyncSession, user_id: uuid.UUID, name: str, domain: str, schema_definition: dict) -> CustomSchema:
    schema = CustomSchema(user_id=user_id, name=name, domain=domain, schema_definition=schema_definition)
    db.add(schema)
    await db.flush()
    return schema


async def list_schemas(db: AsyncSession, user_id: uuid.UUID, page: int, per_page: int):
    return await paginate(
        db,
        select(CustomSchema).where(CustomSchema.user_id == user_id).order_by(CustomSchema.created_at.desc()),
        page, per_page,
    )


async def get_schema(db: AsyncSession, user_id: uuid.UUID, schema_id: uuid.UUID) -> CustomSchema:
    s = await db.get(CustomSchema, schema_id)
    if not s or s.user_id != user_id:
        raise NotFoundError("schema")
    return s


async def update_schema(db: AsyncSession, user_id: uuid.UUID, schema_id: uuid.UUID, **kwargs) -> CustomSchema:
    s = await get_schema(db, user_id, schema_id)
    for k, v in kwargs.items():
        if v is not None:
            setattr(s, k, v)
    await db.flush()
    return s


async def delete_schema(db: AsyncSession, user_id: uuid.UUID, schema_id: uuid.UUID) -> None:
    s = await get_schema(db, user_id, schema_id)
    await db.delete(s)
