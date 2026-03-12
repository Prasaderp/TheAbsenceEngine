from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResponse:
    text: str
    tokens_used: int
    model: str
    latency_ms: float


class LLMGateway(ABC):
    @abstractmethod
    async def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse: ...

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: type[T]) -> T: ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]: ...
