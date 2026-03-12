from app.engine.parsers.base import BaseParser, ParsedDocument, Section


class TextParser(BaseParser):
    async def parse(self, data: bytes, mime_type: str) -> ParsedDocument:
        text = data.decode("utf-8", errors="replace").strip()
        if not text:
            return ParsedDocument(text="", metadata={"empty": True})
        lines = text.splitlines()
        sections: list[Section] = []
        buf: list[str] = []
        current_heading = "Document"
        for line in lines:
            if line.startswith("# "):
                if buf:
                    sections.append(Section(heading=current_heading, text="\n".join(buf).strip(), level=1))
                    buf = []
                current_heading = line.lstrip("# ").strip()
            else:
                buf.append(line)
        if buf:
            sections.append(Section(heading=current_heading, text="\n".join(buf).strip(), level=1))
        return ParsedDocument(text=text, sections=sections, metadata={"char_count": len(text)})
