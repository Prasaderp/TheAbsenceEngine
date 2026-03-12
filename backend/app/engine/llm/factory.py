
from __future__ import annotations

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.config import settings
from app.engine.llm.gateway import LLMGateway, LLMResponse
from app.shared.logger import get_logger

log = get_logger(__name__)


# ── retry decorator factory ────────────────────────────────────────────────────

def _build_retry(provider_name: str):
    def _before_sleep(rs):
        log.warning(
            "LLM retry",
            extra={"provider": provider_name, "attempt": rs.attempt_number},
        )

    return retry(
        stop=stop_after_attempt(settings.llm_max_retries),
        wait=wait_exponential_jitter(initial=1, max=30),
        retry=retry_if_exception_type(Exception),
        before_sleep=_before_sleep,
        reraise=True,
    )


# ── per-provider retry wrapper ─────────────────────────────────────────────────

class _RetryingProvider(LLMGateway):
    """Wraps a single provider with tenacity retry."""

    def __init__(self, inner: LLMGateway, name: str) -> None:
        self._inner = inner
        self._retry = _build_retry(name)

    async def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        return await self._retry(self._inner.generate)(prompt, max_tokens)

    async def generate_structured(self, prompt: str, schema: type) -> object:
        return await self._retry(self._inner.generate_structured)(prompt, schema)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self._retry(self._inner.embed)(texts)


# ── fallback chain ─────────────────────────────────────────────────────────────

class _FallbackGateway(LLMGateway):
    """
    Tries each provider in order.  On any exception, logs the failure and
    delegates to the next provider.  Raises RuntimeError if all fail.
    """

    def __init__(self, chain: list[tuple[str, LLMGateway]]) -> None:
        self._chain = chain

    async def _call(self, method: str, *args, **kwargs):
        last_exc: Exception | None = None
        for name, provider in self._chain:
            try:
                return await getattr(provider, method)(*args, **kwargs)
            except Exception as exc:
                log.warning(
                    "LLM provider failed, trying next",
                    extra={"provider": name, "error": str(exc)},
                )
                last_exc = exc
        raise RuntimeError("All LLM providers failed") from last_exc

    async def generate(self, prompt: str, max_tokens: int = 4096) -> LLMResponse:
        return await self._call("generate", prompt, max_tokens)

    async def generate_structured(self, prompt: str, schema: type) -> object:
        return await self._call("generate_structured", prompt, schema)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self._call("embed", texts)


# ── provider instantiator ──────────────────────────────────────────────────────

def _build_provider(name: str) -> LLMGateway | None:
    """
    Instantiate a provider only when its API key is present.
    Returns None when the key is missing so the caller skips it.
    """
    n = name.strip().lower()
    if n == "gemini":
        if not settings.gemini_api_key:
            log.warning("Gemini API key missing — skipping provider", extra={"provider": "gemini"})
            return None
        from app.engine.llm.gemini_provider import GeminiProvider
        return GeminiProvider()
    if n == "openai":
        if not settings.openai_api_key:
            log.warning("OpenAI API key missing — skipping provider", extra={"provider": "openai"})
            return None
        from app.engine.llm.openai_provider import OpenAIProvider
        return OpenAIProvider()
    if n == "anthropic":
        if not settings.anthropic_api_key:
            log.warning("Anthropic API key missing — skipping provider", extra={"provider": "anthropic"})
            return None
        from app.engine.llm.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    log.warning("Unknown LLM provider name — ignoring", extra={"provider": n})
    return None


# ── public factory ─────────────────────────────────────────────────────────────

def build_gateway() -> LLMGateway:
    """
    Build and return the active LLM gateway.

    Evaluation order: LLM_PRIMARY_PROVIDER → each name in LLM_FALLBACK_CHAIN.
    Providers with missing API keys are silently excluded.
    Raises RuntimeError at startup if no provider is available.
    """
    chain_names: list[str] = [settings.llm_primary_provider]
    if settings.llm_fallback_chain:
        chain_names += [n for n in settings.llm_fallback_chain.split(",") if n.strip()]

    # deduplicate while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for n in chain_names:
        key = n.strip().lower()
        if key and key not in seen:
            seen.add(key)
            ordered.append(key)

    chain: list[tuple[str, LLMGateway]] = []
    for name in ordered:
        provider = _build_provider(name)
        if provider is not None:
            chain.append((name, _RetryingProvider(provider, name)))

    if not chain:
        raise RuntimeError(
            "No LLM providers are configured. "
            "Set at least one of GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY."
        )

    if len(chain) == 1:
        log.info("LLM gateway built", extra={"chain": [chain[0][0]]})
        return chain[0][1]

    log.info("LLM gateway built", extra={"chain": [n for n, _ in chain]})
    return _FallbackGateway(chain)
