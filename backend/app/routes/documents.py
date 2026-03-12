import uuid
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user, rate_limit_upload
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services import document_service
from app.config import settings
from app.shared.errors import ValidationError

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
    _rl: None = Depends(rate_limit_upload),
):
    data = await file.read()
    if len(data) == 0:
        raise ValidationError("File must not be empty.")
    if len(data) > settings.max_upload_bytes:
        raise ValidationError("File exceeds 50 MB limit.")
    mime = file.content_type or "application/octet-stream"
    doc = await document_service.upload_document(
        db, user_id, file.filename or "upload", mime, data
    )
    return DocumentResponse.model_validate(doc)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    docs, meta = await document_service.list_documents(db, user_id, page, per_page)
    return DocumentListResponse(
        data=[DocumentResponse.model_validate(d) for d in docs],
        meta=meta,
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    doc = await document_service.get_document(db, user_id, doc_id)
    return DocumentResponse.model_validate(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user),
):
    await document_service.delete_document(db, user_id, doc_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
