import time
from typing import TypeVar
from pydantic import BaseModel
from openai import AsyncOpenAI
from app.engine.llm.gateway import LLMGateway, LLMResponse
from app.config import settings

T = TypeVar("T", bound=BaseModel)


class OpenAIProvider(LLMGateway):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = "gpt-4o-mini"
        self._embed_model = "text-embedding-3-large"

    async def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        t0 = time.monotonic()
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return LLMResponse(
            text=resp.choices[0].message.content or "",
            tokens_used=resp.usage.total_tokens if resp.usage else 0,
            model=self._model,
            latency_ms=(time.monotonic() - t0) * 1000,
        )

    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        resp = await self._client.beta.chat.completions.parse(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format=schema,
        )
        return resp.choices[0].message.parsed

    async def embed(self, texts: list[str]) -> list[list[float]]:
        resp = await self._client.embeddings.create(
            model=self._embed_model,
            input=texts,
            dimensions=settings.embedding_dimensions,
        )
        return [e.embedding for e in resp.data]
