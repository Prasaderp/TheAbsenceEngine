import time
import json
from typing import TypeVar
from pydantic import BaseModel
from google import genai
from google.genai import types as gtypes
from app.engine.llm.gateway import LLMGateway, LLMResponse
from app.config import settings
from app.shared.logger import get_logger

log = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiProvider(LLMGateway):
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.llm_model
        self._embed_model = settings.embedding_model

    async def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        t0 = time.monotonic()
        resp = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=gtypes.GenerateContentConfig(max_output_tokens=max_tokens),
        )
        latency = (time.monotonic() - t0) * 1000
        usage = resp.usage_metadata
        return LLMResponse(
            text=resp.text or "",
            tokens_used=(usage.total_token_count or 0) if usage else 0,
            model=self._model,
            latency_ms=latency,
        )

    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        t0 = time.monotonic()
        resp = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=gtypes.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        latency = (time.monotonic() - t0) * 1000
        log.info("gemini structured call", extra={"latency_ms": round(latency, 1)})
        return schema.model_validate_json(resp.text or "{}")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        result = await self._client.aio.models.embed_content(
            model=self._embed_model,
            contents=texts,
        )
        return [e.values for e in result.embeddings]
