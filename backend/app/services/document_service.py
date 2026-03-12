import uuid
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
from app.shared.pagination import paginate, PageMeta
from app.shared.errors import NotFoundError
from app.shared import storage
from app.engine.parsers import get_parser, validate_mime
from app.shared.logger import get_logger

log = get_logger(__name__)

ALLOWED_MIME = {
    "text/plain", "text/markdown", "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


async def upload_document(
    session: AsyncSession,
    user_id: uuid.UUID,
    filename: str,
    mime_type: str,
    data: bytes,
) -> Document:
    validate_mime(mime_type)

    checksum = storage.sha256(data)
    key = storage.build_key(str(user_id), filename)
    await storage.upload(data, key, mime_type)

    parser = get_parser(mime_type)
    parsed = await parser.parse(data, mime_type)

    doc = Document(
        user_id=user_id,
        filename=filename,
        mime_type=mime_type,
        storage_key=key,
        size_bytes=len(data),
        extracted_text=parsed.text or None,
        checksum_sha256=checksum,
    )
    session.add(doc)
    await session.flush()
    log.info("Document uploaded", extra={"user_id": str(user_id), "doc_id": str(doc.id)})
    return doc


async def list_documents(
    session: AsyncSession,
    user_id: uuid.UUID,
    page: int,
    per_page: int,
) -> tuple[list[Document], PageMeta]:
    q: Select = (
        select(Document)
        .where(Document.user_id == user_id, Document.is_deleted.is_(False))
        .order_by(Document.created_at.desc())
    )
    rows, meta = await paginate(session, q, page, per_page)
    return list(rows), meta


async def get_document(
    session: AsyncSession,
    user_id: uuid.UUID,
    doc_id: uuid.UUID,
) -> Document:
    doc = await session.get(Document, doc_id)
    if not doc or doc.is_deleted or doc.user_id != user_id:
        raise NotFoundError("document")
    return doc


async def delete_document(
    session: AsyncSession,
    user_id: uuid.UUID,
    doc_id: uuid.UUID,
) -> None:
    doc = await get_document(session, user_id, doc_id)
    doc.is_deleted = True
    await storage.delete(doc.storage_key)
    log.info("Document deleted", extra={"user_id": str(user_id), "doc_id": str(doc_id)})
