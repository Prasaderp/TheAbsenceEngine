from app.engine.parsers.base import BaseParser
from app.engine.parsers.text_parser import TextParser
from app.engine.parsers.pdf_parser import PDFParser
from app.engine.parsers.docx_parser import DocxParser
from app.engine.parsers.csv_parser import CSVParser, XLSXParser
from app.shared.errors import ValidationError

_ALLOWED: dict[str, type[BaseParser]] = {
    "text/plain": TextParser,
    "text/markdown": TextParser,
    "application/pdf": PDFParser,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocxParser,
    "text/csv": CSVParser,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": XLSXParser,
}

MAX_SIZE = 52_428_800  # 50 MB


def get_parser(mime_type: str) -> BaseParser:
    cls = _ALLOWED.get(mime_type)
    if not cls:
        raise ValidationError(f"Unsupported file type: {mime_type}")
    return cls()


def validate_mime(mime_type: str) -> None:
    if mime_type not in _ALLOWED:
        raise ValidationError(f"Unsupported file type: {mime_type}")
