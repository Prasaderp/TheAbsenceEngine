import hashlib
import uuid
from pathlib import Path

import aiofiles
import aiofiles.os

from app.config import settings
from app.shared.errors import StorageError
from app.shared.logger import get_logger

log = get_logger(__name__)

_ROOT = Path(settings.local_storage_dir)


def _resolve(key: str) -> Path:
    """Turn a storage key into an absolute, jail-checked path."""
    target = (_ROOT / key).resolve()
    if not str(target).startswith(str(_ROOT.resolve())):
        raise StorageError("Invalid storage key.")
    return target


def build_key(user_id: str, filename: str) -> str:
    """Return a deterministic, unique storage key for a new upload."""
    safe_name = Path(filename).name  # strip any path components from client
    return f"documents/{user_id}/{uuid.uuid4()}/{safe_name}"


async def upload(data: bytes, key: str, content_type: str) -> str:  # noqa: ARG001
    """Persist *data* to local disk at *key*. Returns *key* on success."""
    path = _resolve(key)
    try:
        await aiofiles.os.makedirs(path.parent, exist_ok=True)
        async with aiofiles.open(path, "wb") as fh:
            await fh.write(data)
        log.info("local upload ok", extra={"key": key, "bytes": len(data)})
        return key
    except OSError as exc:
        log.error("local upload failed", extra={"key": key, "error": str(exc)})
        raise StorageError("File upload failed.") from exc


async def get_bytes(key: str) -> bytes:
    """Read and return the file at *key*."""
    path = _resolve(key)
    try:
        async with aiofiles.open(path, "rb") as fh:
            return await fh.read()
    except FileNotFoundError as exc:
        log.error("local file not found", extra={"key": key})
        raise StorageError("File not found.") from exc
    except OSError as exc:
        log.error("local read failed", extra={"key": key, "error": str(exc)})
        raise StorageError("File download failed.") from exc


async def delete(key: str) -> None:
    """Remove the file at *key*. Idempotent — missing file is not an error."""
    path = _resolve(key)
    try:
        await aiofiles.os.remove(path)
        log.info("local delete ok", extra={"key": key})
    except FileNotFoundError:
        pass  # Already gone — idempotent by design
    except OSError as exc:
        log.error("local delete failed", extra={"key": key, "error": str(exc)})
        raise StorageError("File deletion failed.") from exc


def sha256(data: bytes) -> str:
    """Return the hex SHA-256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()
