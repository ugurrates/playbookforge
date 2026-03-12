"""
OpenAI LLM Client — Cloud LLM inference via OpenAI API.
Default model: gpt-4o.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

import httpx

from .adapter import LLMAdapter

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIClient(LLMAdapter):
    """LLM adapter for OpenAI API (GPT-4o, GPT-4, GPT-3.5-turbo)."""

    name = "openai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

        if not self.api_key:
            logger.warning("No OpenAI API key configured. Set OPENAI_API_KEY environment variable.")

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
        """Generate text using OpenAI Chat Completions API."""
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not configured. "
                "Set OPENAI_API_KEY environment variable or pass api_key to constructor."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 4096,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        client = self._get_client()

        try:
            response = await client.post(OPENAI_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid OpenAI API key.")
            raise RuntimeError(f"OpenAI API error: {e.response.status_code} — {e.response.text}")
        except httpx.TimeoutException:
            raise ConnectionError(
                f"OpenAI request timed out after {self.timeout}s. "
                "Try again or check your network connection."
            )

    async def is_available(self) -> bool:
        """Check if OpenAI API is reachable with the configured key."""
        if not self.api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            check_client = httpx.AsyncClient(timeout=5.0)
            try:
                response = await check_client.get("https://api.openai.com/v1/models", headers=headers)
                return response.status_code == 200
            finally:
                await check_client.aclose()
        except Exception:
            return False
