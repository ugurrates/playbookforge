"""
PlaybookForge LLM Integration.
Provides a unified interface for AI-powered playbook generation.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from .adapter import LLMAdapter
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient
from .claude_client import ClaudeClient

logger = logging.getLogger(__name__)

__all__ = ["LLMAdapter", "OllamaClient", "OpenAIClient", "ClaudeClient", "get_llm_client"]


def get_llm_client(model: str = "auto") -> LLMAdapter:
    """
    Get an LLM client based on configuration.

    Args:
        model: One of "auto", "ollama", "openai", "claude", or a specific model name.
              "auto" will try: Claude (if API key set) -> OpenAI (if API key set) -> Ollama (local).

    Returns:
        An LLMAdapter instance ready to use.
    """
    model = model.lower().strip()

    if model == "ollama" or model.startswith("qwen") or model.startswith("llama") or model.startswith("mistral"):
        ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
        ollama_model = model if model != "ollama" else os.environ.get("OLLAMA_MODEL", "qwen2.5-coder")
        return OllamaClient(base_url=ollama_url, model=ollama_model)

    if model == "openai" or model.startswith("gpt"):
        api_key = os.environ.get("OPENAI_API_KEY", "")
        openai_model = model if model.startswith("gpt") else os.environ.get("OPENAI_MODEL", "gpt-4o")
        return OpenAIClient(api_key=api_key, model=openai_model)

    if model == "claude" or model.startswith("claude"):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        claude_model = model if model.startswith("claude-") else os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        return ClaudeClient(api_key=api_key, model=claude_model)

    if model == "auto":
        # Priority: Claude -> OpenAI -> Ollama
        if os.environ.get("ANTHROPIC_API_KEY"):
            logger.info("Auto-detected Anthropic API key, using Claude.")
            return ClaudeClient()
        if os.environ.get("OPENAI_API_KEY"):
            logger.info("Auto-detected OpenAI API key, using OpenAI.")
            return OpenAIClient()
        logger.info("No cloud API keys found, falling back to Ollama (local).")
        return OllamaClient()

    # Fall back to Ollama with whatever model name was given
    return OllamaClient(model=model)
