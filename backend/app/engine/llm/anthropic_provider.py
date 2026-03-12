import time
from typing import TypeVar
import json
from pydantic import BaseModel
import anthropic
from app.engine.llm.gateway import LLMGateway, LLMResponse
from app.config import settings

T = TypeVar("T", bound=BaseModel)


class AnthropicProvider(LLMGateway):
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = "claude-3-5-haiku-latest"

    async def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        t0 = time.monotonic()
        resp = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(
            text=resp.content[0].text if resp.content else "",
            tokens_used=resp.usage.input_tokens + resp.usage.output_tokens,
            model=self._model,
            latency_ms=(time.monotonic() - t0) * 1000,
        )

    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        full_prompt = f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{schema_json}"
        resp = await self.generate(full_prompt, max_tokens=4096)
        start = resp.text.find("{")
        end = resp.text.rfind("}") + 1
        return schema.model_validate_json(resp.text[start:end])

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not provide an embedding API")
