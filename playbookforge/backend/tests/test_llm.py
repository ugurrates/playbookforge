"""
Tests for LLM integration module.
Tests the adapter pattern, JSON extraction, client factory, and API endpoints.
Note: Actual LLM calls are mocked since we can't depend on external services in CI.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from backend.llm.adapter import LLMAdapter
from backend.llm.ollama_client import OllamaClient
from backend.llm.openai_client import OpenAIClient
from backend.llm.claude_client import ClaudeClient
from backend.llm import get_llm_client


# ============================================================================
# JSON Extraction Tests
# ============================================================================

class TestJSONExtraction:
    """Test the _extract_json static method on LLMAdapter."""

    def test_extract_plain_json(self):
        text = '{"type": "playbook", "name": "Test"}'
        result = LLMAdapter._extract_json(text)
        assert result["type"] == "playbook"
        assert result["name"] == "Test"

    def test_extract_json_from_markdown_code_block(self):
        text = 'Here is the playbook:\n```json\n{"type": "playbook", "name": "Test"}\n```\nDone.'
        result = LLMAdapter._extract_json(text)
        assert result["type"] == "playbook"

    def test_extract_json_from_generic_code_block(self):
        text = 'Result:\n```\n{"type": "playbook"}\n```'
        result = LLMAdapter._extract_json(text)
        assert result["type"] == "playbook"

    def test_extract_json_with_surrounding_text(self):
        text = 'I generated this playbook for you:\n\n{"type": "playbook", "id": "playbook--123"}\n\nHope this helps!'
        result = LLMAdapter._extract_json(text)
        assert result["type"] == "playbook"

    def test_extract_json_with_whitespace(self):
        text = '  \n\n  {"key": "value"}  \n  '
        result = LLMAdapter._extract_json(text)
        assert result["key"] == "value"

    def test_extract_json_invalid_raises(self):
        text = "This is not JSON at all, just plain text."
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            LLMAdapter._extract_json(text)

    def test_extract_nested_json(self):
        data = {"type": "playbook", "workflow": {"step1": {"type": "action"}}}
        text = json.dumps(data)
        result = LLMAdapter._extract_json(text)
        assert "workflow" in result
        assert result["workflow"]["step1"]["type"] == "action"


# ============================================================================
# Client Factory Tests
# ============================================================================

class TestGetLLMClient:
    """Test the get_llm_client factory function."""

    def test_auto_no_keys_returns_ollama(self):
        with patch.dict("os.environ", {}, clear=True):
            # Remove any API keys
            import os
            env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY")}
            with patch.dict("os.environ", env, clear=True):
                client = get_llm_client("auto")
                assert isinstance(client, OllamaClient)

    def test_auto_with_anthropic_key(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-test-123"}):
            client = get_llm_client("auto")
            assert isinstance(client, ClaudeClient)

    def test_auto_with_openai_key(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-123"}, clear=False):
            # Make sure ANTHROPIC_API_KEY is not set
            import os
            env = dict(os.environ)
            env.pop("ANTHROPIC_API_KEY", None)
            env["OPENAI_API_KEY"] = "sk-test-123"
            with patch.dict("os.environ", env, clear=True):
                client = get_llm_client("auto")
                assert isinstance(client, OpenAIClient)

    def test_explicit_ollama(self):
        client = get_llm_client("ollama")
        assert isinstance(client, OllamaClient)

    def test_explicit_openai(self):
        client = get_llm_client("openai")
        assert isinstance(client, OpenAIClient)

    def test_explicit_claude(self):
        client = get_llm_client("claude")
        assert isinstance(client, ClaudeClient)

    def test_specific_model_gpt(self):
        client = get_llm_client("gpt-4o")
        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4o"

    def test_specific_model_claude(self):
        client = get_llm_client("claude-sonnet-4-20250514")
        assert isinstance(client, ClaudeClient)

    def test_specific_model_qwen(self):
        client = get_llm_client("qwen2.5-coder")
        assert isinstance(client, OllamaClient)
        assert client.model == "qwen2.5-coder"

    def test_unknown_model_falls_back_to_ollama(self):
        client = get_llm_client("some-custom-model")
        assert isinstance(client, OllamaClient)
        assert client.model == "some-custom-model"


# ============================================================================
# Ollama Client Tests
# ============================================================================

class TestOllamaClient:
    """Test OllamaClient properties and configuration."""

    def test_default_config(self):
        client = OllamaClient()
        assert client.name == "ollama"
        assert client.model == "qwen2.5-coder"
        assert client.base_url == "http://localhost:11434"

    def test_custom_config(self):
        client = OllamaClient(base_url="http://ollama:11434", model="llama3.2")
        assert client.base_url == "http://ollama:11434"
        assert client.model == "llama3.2"


# ============================================================================
# OpenAI Client Tests
# ============================================================================

class TestOpenAIClient:
    """Test OpenAIClient properties and configuration."""

    def test_default_config(self):
        client = OpenAIClient(api_key="test-key")
        assert client.name == "openai"
        assert client.model == "gpt-4o"
        assert client.api_key == "test-key"

    def test_no_key_warning(self):
        with patch.dict("os.environ", {}, clear=True):
            import os
            env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
            with patch.dict("os.environ", env, clear=True):
                client = OpenAIClient()
                assert client.api_key == ""

    @pytest.mark.asyncio
    async def test_generate_without_key_raises(self):
        client = OpenAIClient(api_key="")
        with pytest.raises(ValueError, match="API key not configured"):
            await client.generate("test prompt")


# ============================================================================
# Claude Client Tests
# ============================================================================

class TestClaudeClient:
    """Test ClaudeClient properties and configuration."""

    def test_default_config(self):
        client = ClaudeClient(api_key="test-key")
        assert client.name == "claude"
        assert "claude" in client.model
        assert client.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_generate_without_key_raises(self):
        client = ClaudeClient(api_key="")
        with pytest.raises(ValueError, match="API key not configured"):
            await client.generate("test prompt")


# ============================================================================
# LLM Adapter Integration Tests (mocked)
# ============================================================================

class TestLLMAdapterMocked:
    """Test generate_playbook, enrich, analyze with mocked LLM responses."""

    @pytest.mark.asyncio
    async def test_generate_playbook_happy_path(self):
        """Test that a valid JSON response is returned from generate_playbook."""
        mock_playbook = {
            "type": "playbook",
            "spec_version": "cacao-2.0",
            "id": "playbook--test-123",
            "name": "Test Playbook",
            "created_by": "identity--test",
            "created": "2024-01-01T00:00:00Z",
            "modified": "2024-01-01T00:00:00Z",
            "workflow_start": "start--1",
            "workflow": {
                "start--1": {"type": "start", "name": "Start", "on_completion": "end--1"},
                "end--1": {"type": "end", "name": "End"},
            },
        }

        client = OllamaClient()
        client.generate = AsyncMock(return_value=json.dumps(mock_playbook))

        result = await client.generate_playbook("Create a test playbook")
        assert result["type"] == "playbook"
        assert result["name"] == "Test Playbook"

    @pytest.mark.asyncio
    async def test_generate_playbook_from_code_block(self):
        """Test JSON extraction from markdown code block."""
        mock_response = '```json\n{"type": "playbook", "name": "Test"}\n```'

        client = OllamaClient()
        client.generate = AsyncMock(return_value=mock_response)

        result = await client.generate_playbook("Create a test playbook")
        assert result["type"] == "playbook"

    @pytest.mark.asyncio
    async def test_enrich_playbook(self):
        """Test playbook enrichment."""
        enriched = {"type": "playbook", "name": "Enriched Playbook", "description": "Now with descriptions!"}

        client = OllamaClient()
        client.generate = AsyncMock(return_value=json.dumps(enriched))

        result = await client.enrich_playbook({"type": "playbook", "name": "Basic"})
        assert result["name"] == "Enriched Playbook"

    @pytest.mark.asyncio
    async def test_analyze_playbook_json(self):
        """Test playbook analysis returning JSON."""
        analysis = {"overall_score": 75, "strengths": ["Good structure"], "weaknesses": ["Missing descriptions"]}

        client = OllamaClient()
        client.generate = AsyncMock(return_value=json.dumps(analysis))

        result = await client.analyze_playbook({"type": "playbook"})
        assert result["overall_score"] == 75

    @pytest.mark.asyncio
    async def test_analyze_playbook_text_fallback(self):
        """Test playbook analysis falling back to text when JSON parsing fails."""
        client = OllamaClient()
        client.generate = AsyncMock(return_value="This playbook looks good overall.")

        result = await client.analyze_playbook({"type": "playbook"})
        assert result["format"] == "text"
        assert "good overall" in result["analysis"]


# ============================================================================
# API Endpoint Tests (mocked LLM)
# ============================================================================

class TestAIEndpoints:
    """Test the /ai/* FastAPI endpoints with mocked LLM."""

    @pytest.mark.asyncio
    async def test_ai_generate_endpoint(self):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app

        mock_playbook = {"type": "playbook", "name": "Generated"}

        with patch("backend.main.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_client.generate_playbook = AsyncMock(return_value=mock_playbook)
            mock_client.name = "ollama"
            mock_client.model = "qwen2.5-coder"
            mock_get.return_value = mock_client

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/ai/generate", json={
                    "prompt": "Create a phishing playbook",
                    "model": "auto",
                })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["playbook"]["name"] == "Generated"
            assert "ollama" in data["model_used"]

    @pytest.mark.asyncio
    async def test_ai_enrich_endpoint(self):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app

        enriched = {"type": "playbook", "name": "Enriched"}

        with patch("backend.main.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_client.enrich_playbook = AsyncMock(return_value=enriched)
            mock_client.name = "openai"
            mock_client.model = "gpt-4o"
            mock_get.return_value = mock_client

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/ai/enrich", json={
                    "playbook": {"type": "playbook"},
                    "model": "openai",
                })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["playbook"]["name"] == "Enriched"

    @pytest.mark.asyncio
    async def test_ai_analyze_endpoint(self):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app

        analysis = {"overall_score": 85, "strengths": ["Well structured"]}

        with patch("backend.main.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_client.analyze_playbook = AsyncMock(return_value=analysis)
            mock_client.name = "claude"
            mock_client.model = "claude-sonnet-4-20250514"
            mock_get.return_value = mock_client

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/ai/analyze", json={
                    "playbook": {"type": "playbook"},
                    "model": "claude",
                })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["analysis"]["overall_score"] == 85

    @pytest.mark.asyncio
    async def test_ai_generate_connection_error(self):
        from httpx import AsyncClient, ASGITransport
        from backend.main import app

        with patch("backend.main.get_llm_client") as mock_get:
            mock_client = MagicMock()
            mock_client.generate_playbook = AsyncMock(side_effect=ConnectionError("Cannot connect to Ollama"))
            mock_client.name = "ollama"
            mock_client.model = "qwen2.5-coder"
            mock_get.return_value = mock_client

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/ai/generate", json={
                    "prompt": "Test",
                    "model": "auto",
                })

            assert response.status_code == 503
