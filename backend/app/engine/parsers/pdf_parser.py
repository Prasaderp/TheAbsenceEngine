import io
import pdfplumber
from app.engine.parsers.base import BaseParser, ParsedDocument, Section
from app.shared.errors import ValidationError


class PDFParser(BaseParser):
    async def parse(self, data: bytes, mime_type: str) -> ParsedDocument:
        try:
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                if not pdf.pages:
                    raise ValidationError("PDF file is empty or could not be read.")
                pages: list[str] = []
                for i, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    if text.strip():
                        pages.append(f"[Page {i}]\n{text.strip()}")
                full_text = "\n\n".join(pages)
                if not full_text.strip():
                    raise ValidationError("PDF contains no extractable text. It may be a scanned document.")
                sections = [
                    Section(heading=f"Page {i + 1}", text=p.split("\n", 1)[-1], level=1)
                    for i, p in enumerate(pages)
                ]
                return ParsedDocument(
                    text=full_text,
                    sections=sections,
                    metadata={"page_count": len(pdf.pages)},
                )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"PDF parsing failed: {e}") from e
