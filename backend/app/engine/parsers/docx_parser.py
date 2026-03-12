import io
import docx
from app.engine.parsers.base import BaseParser, ParsedDocument, Section
from app.shared.errors import ValidationError


class DocxParser(BaseParser):
    async def parse(self, data: bytes, mime_type: str) -> ParsedDocument:
        try:
            doc = docx.Document(io.BytesIO(data))
            sections: list[Section] = []
            buf: list[str] = []
            current_heading = "Document"
            level = 1

            for para in doc.paragraphs:
                style = para.style.name if para.style else ""
                text = para.text.strip()
                if style.startswith("Heading") and text:
                    if buf:
                        sections.append(Section(heading=current_heading, text="\n".join(buf), level=level))
                        buf = []
                    try:
                        level = int(style.split()[-1])
                    except ValueError:
                        level = 1
                    current_heading = text
                elif text:
                    buf.append(text)

            if buf:
                sections.append(Section(heading=current_heading, text="\n".join(buf), level=level))

            full_text = "\n\n".join(
                f"{s.heading}\n{s.text}" if s.heading != "Document" else s.text
                for s in sections
            )
            if not full_text.strip():
                raise ValidationError("DOCX file contains no extractable text.")
            return ParsedDocument(
                text=full_text,
                sections=sections,
                metadata={"paragraph_count": len(doc.paragraphs)},
            )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"DOCX parsing failed: {e}") from e
