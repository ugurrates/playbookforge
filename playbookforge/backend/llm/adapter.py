"""
LLM Adapter — Base class for all LLM integrations.
Provides a common interface for Ollama, OpenAI, and Claude backends.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from ..core.cacao_model import CacaoPlaybook
from ..core.validator import CacaoValidator

logger = logging.getLogger(__name__)


class LLMAdapter(ABC):
    """Abstract base class for LLM integrations."""

    name: str = "base"
    model: str = ""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Send a prompt to the LLM and return the raw text response."""
        ...

    async def generate_playbook(
        self,
        description: str,
        product_ids: Optional[list[str]] = None,
    ) -> dict:
        """Generate a CACAO playbook from a natural language description.

        If product_ids are provided, the prompt is enriched with product/action
        definitions so the LLM generates executable, product-aware commands.
        """
        from .prompts import NL_TO_CACAO_PROMPT, build_product_context

        system_prompt = NL_TO_CACAO_PROMPT

        # Inject product context into system prompt when products are selected
        if product_ids:
            from ..core.products import product_catalog
            product_context = build_product_context(product_ids, product_catalog)
            if product_context:
                system_prompt = system_prompt + "\n" + product_context

        user_prompt = f"Generate a CACAO v2.0 playbook for the following description:\n\n{description}"

        raw = await self.generate(user_prompt, system_prompt=system_prompt)
        playbook_json = self._extract_json(raw)

        # Validate and optionally retry
        try:
            playbook = CacaoPlaybook(**playbook_json)
            validator = CacaoValidator()
            result = validator.validate(playbook)
            if result.errors:
                logger.warning(
                    "Generated playbook has %d validation errors, attempting fix...",
                    len(result.errors),
                )
                playbook_json = await self._fix_playbook(playbook_json, result.to_dict(), description)
        except Exception as e:
            logger.warning("Generated playbook failed parsing: %s", e)

        return playbook_json

    async def enrich_playbook(self, playbook_dict: dict) -> dict:
        """Enrich/improve an existing CACAO playbook."""
        from .prompts import ENRICH_PROMPT

        system_prompt = ENRICH_PROMPT
        user_prompt = (
            "Enrich and improve the following CACAO v2.0 playbook. "
            "Add missing descriptions, suggest additional steps, and add MITRE ATT&CK references where appropriate.\n\n"
            f"```json\n{json.dumps(playbook_dict, indent=2)}\n```"
        )

        raw = await self.generate(user_prompt, system_prompt=system_prompt)
        return self._extract_json(raw)

    async def analyze_playbook(self, playbook_dict: dict) -> dict:
        """Analyze a CACAO playbook and return a quality report."""
        from .prompts import ANALYZE_PROMPT

        system_prompt = ANALYZE_PROMPT

        playbook_json_str = json.dumps(playbook_dict, indent=2)
        user_prompt = (
            "Analyze the following CACAO v2.0 playbook and provide a detailed quality report.\n\n"
            f"```json\n{playbook_json_str}\n```"
        )

        raw = await self.generate(user_prompt, system_prompt=system_prompt)

        # Try to parse as JSON report, fall back to text
        try:
            return self._extract_json(raw)
        except Exception:
            return {
                "analysis": raw,
                "format": "text",
            }

    async def _fix_playbook(self, playbook_dict: dict, validation_result: dict, original_description: str) -> dict:
        """Attempt to fix validation errors in a generated playbook."""
        errors = [
            issue for issue in validation_result.get("issues", [])
            if issue.get("severity") == "error"
        ]
        error_summary = "\n".join(f"- [{e['code']}] {e['message']}" for e in errors[:10])

        fix_prompt = (
            "The following CACAO v2.0 playbook has validation errors. "
            "Fix ALL errors and return a valid CACAO v2.0 JSON playbook.\n\n"
            f"Original description: {original_description}\n\n"
            f"Validation errors:\n{error_summary}\n\n"
            f"Current playbook:\n```json\n{json.dumps(playbook_dict, indent=2)}\n```\n\n"
            "Return ONLY the fixed JSON playbook, no explanation."
        )

        raw = await self.generate(fix_prompt)
        try:
            return self._extract_json(raw)
        except Exception:
            return playbook_dict

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract JSON object from LLM response text."""
        # Try direct JSON parse first
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        for marker in ["```json", "```"]:
            if marker in text:
                start = text.index(marker) + len(marker)
                end = text.index("```", start) if "```" in text[start:] else len(text)
                candidate = text[start:end].strip()
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        # Try to find JSON object boundaries
        brace_start = text.find("{")
        brace_end = text.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            candidate = text[brace_start : brace_end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract valid JSON from LLM response (length={len(text)})")
