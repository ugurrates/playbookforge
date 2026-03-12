"""
Ollama LLM Client — Local LLM inference via Ollama API.
Default model: qwen2.5-coder (good for JSON generation).
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from .adapter import LLMAdapter

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder"


class OllamaClient(LLMAdapter):
    """LLM adapter for Ollama local inference."""

    name = "ollama"

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = 180.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._model_resolved: bool = False

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create a persistent async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5,
                    keepalive_expiry=30,
                ),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Ollama API."""
        # Auto-resolve model name on first call (e.g. "qwen2.5-coder" -> "qwen2.5-coder:14b")
        if not self._model_resolved:
            resolved = await self._resolve_model()
            if resolved and resolved != self.model:
                logger.info(f"Resolved Ollama model '{self.model}' -> '{resolved}'")
                self.model = resolved
            self._model_resolved = True

        payload: dict = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 4096,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        url = f"{self.base_url}/api/generate"
        client = self._get_client()

        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except httpx.ConnectError:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running: `ollama serve`"
            )
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Ollama API error: {e.response.status_code} — {e.response.text}")
        except httpx.TimeoutException:
            raise ConnectionError(
                f"Ollama request timed out after {self.timeout}s. "
                "The model may be loading or the prompt may be too long."
            )

    async def _resolve_model(self) -> str | None:
        """Find the best matching model name from Ollama's model list."""
        try:
            check_client = httpx.AsyncClient(timeout=5.0)
            try:
                response = await check_client.get(f"{self.base_url}/api/tags")
                if response.status_code != 200:
                    return None
                models = [m.get("name", "") for m in response.json().get("models", [])]
                # Exact match first
                if self.model in models:
                    return self.model
                # Match without tag (e.g. "qwen2.5-coder" matches "qwen2.5-coder:14b")
                for m in models:
                    if m.split(":")[0] == self.model or m.startswith(self.model + ":"):
                        return m
                return None
            finally:
                await check_client.aclose()
        except Exception:
            return None

    async def is_available(self) -> bool:
        """Check if Ollama is running and the model is available."""
        return (await self._resolve_model()) is not None
