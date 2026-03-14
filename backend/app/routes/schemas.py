import uuid
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.schemas.custom_schema import SchemaCreateRequest, SchemaResponse, SchemaListResponse, SchemaUpdateRequest
from app.services import schema_service

router = APIRouter()


@router.post("", response_model=SchemaResponse, status_code=status.HTTP_201_CREATED)
async def create_schema(
    body: SchemaCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    schema = await schema_service.create_schema(db, user_id, body.name, body.domain, body.schema_definition)
    return SchemaResponse.model_validate(schema)


@router.get("", response_model=SchemaListResponse)
async def list_schemas(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    schemas, meta = await schema_service.list_schemas(db, user_id, page, per_page)
    return SchemaListResponse(data=[SchemaResponse.model_validate(s) for s in schemas], meta=meta)


@router.get("/{schema_id}", response_model=SchemaResponse)
async def get_schema(
    schema_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    return SchemaResponse.model_validate(await schema_service.get_schema(db, user_id, schema_id))


@router.put("/{schema_id}", response_model=SchemaResponse)
async def update_schema(
    schema_id: uuid.UUID,
    body: SchemaUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    schema = await schema_service.update_schema(db, user_id, schema_id, **body.model_dump(exclude_none=True))
    return SchemaResponse.model_validate(schema)


@router.delete("/{schema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schema(
    schema_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    await schema_service.delete_schema(db, user_id, schema_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
