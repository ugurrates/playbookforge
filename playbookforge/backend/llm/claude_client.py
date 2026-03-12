"""
Anthropic Claude LLM Client — Cloud LLM inference via Anthropic Messages API.
Default model: claude-sonnet-4-20250514.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

import httpx

from .adapter import LLMAdapter

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class ClaudeClient(LLMAdapter):
    """LLM adapter for Anthropic Claude API."""

    name = "claude"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

        if not self.api_key:
            logger.warning("No Anthropic API key configured. Set ANTHROPIC_API_KEY environment variable.")

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
        """Generate text using Anthropic Messages API."""
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not configured. "
                "Set ANTHROPIC_API_KEY environment variable or pass api_key to constructor."
            )

        payload: dict = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }

        if system_prompt:
            payload["system"] = system_prompt

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": API_VERSION,
            "Content-Type": "application/json",
        }

        client = self._get_client()

        try:
            response = await client.post(ANTHROPIC_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Extract text from content blocks
            content_blocks = data.get("content", [])
            text_parts = [block["text"] for block in content_blocks if block.get("type") == "text"]
            return "\n".join(text_parts)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid Anthropic API key.")
            raise RuntimeError(f"Anthropic API error: {e.response.status_code} — {e.response.text}")
        except httpx.TimeoutException:
            raise ConnectionError(
                f"Anthropic request timed out after {self.timeout}s. "
                "Try again or check your network connection."
            )

    async def is_available(self) -> bool:
        """Check if Anthropic API is reachable with the configured key."""
        if not self.api_key:
            return False
        try:
            # Simple test — try to hit the API
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": API_VERSION,
            }
            check_client = httpx.AsyncClient(timeout=5.0)
            try:
                # Use a minimal request to test auth
                response = await check_client.post(
                    ANTHROPIC_API_URL,
                    json={
                        "model": self.model,
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "hi"}],
                    },
                    headers={**headers, "Content-Type": "application/json"},
                )
                return response.status_code == 200
            finally:
                await check_client.aclose()
        except Exception:
            return False
