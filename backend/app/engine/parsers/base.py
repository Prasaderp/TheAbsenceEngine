from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Section:
    heading: str
    text: str
    level: int = 1


@dataclass
class ParsedDocument:
    text: str
    sections: list[Section] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class BaseParser(ABC):
    @abstractmethod
    async def parse(self, data: bytes, mime_type: str) -> ParsedDocument:
        ...
