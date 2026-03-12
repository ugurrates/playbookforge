"""
LLM Prompt Templates for PlaybookForge.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.products import ProductCatalog

_PROMPTS_DIR = Path(__file__).parent


def _load(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")


NL_TO_CACAO_PROMPT = _load("nl_to_cacao.txt")
ENRICH_PROMPT = _load("enrich.txt")
ANALYZE_PROMPT = _load("analyze.txt")


def build_product_context(product_ids: list[str], catalog: "ProductCatalog") -> str:
    """Build a product-aware context block to inject into the LLM prompt.

    For each selected product, includes vendor info and available actions
    with their HTTP method, endpoint pattern, and parameters so the LLM
    can generate realistic, executable CACAO commands.
    """
    if not product_ids:
        return ""

    sections: list[str] = []
    sections.append("\n## Available Security Products & Actions")
    sections.append("Use ONLY the following products and their API actions in the generated playbook.")
    sections.append("Each action step MUST use `http-api` command type with the given endpoint pattern.\n")

    for pid in product_ids:
        product = catalog.get(pid)
        if not product:
            continue

        sections.append(f"### {product.name} ({product.vendor})")
        sections.append(f"Category: {product.category.value}")
        sections.append(f"Base URL: {product.base_url_pattern}")
        sections.append(f"Auth: {', '.join(a.value for a in product.auth_types)}")
        sections.append("")

        for action in product.actions:
            params_str = ""
            if action.parameters:
                param_items = []
                for p in action.parameters:
                    req = "*" if p.required else ""
                    example = f' (e.g. "{p.example}")' if p.example else ""
                    param_items.append(f"    - {p.name}{req}: {p.type} — {p.description}{example}")
                params_str = "\n" + "\n".join(param_items)

            sections.append(f"- **{action.name}** (`{action.id}`)")
            sections.append(f"  {action.description}")
            sections.append(f"  `{action.http_method} {action.endpoint_pattern}`{params_str}")
            sections.append("")

    sections.append("## IMPORTANT RULES FOR PRODUCT USAGE")
    sections.append("1. ONLY use the products and actions listed above")
    sections.append("2. Each action step command MUST be type 'http-api'")
    sections.append("3. Use the exact endpoint pattern from the product definition")
    sections.append("4. Include required parameters in the command content as JSON")
    sections.append("5. Use playbook variables (e.g. __api_key__, __base_url__) for credentials and dynamic values")
    sections.append("6. Reference the product and action in the step name (e.g. 'CrowdStrike: Isolate Host')")
    sections.append("")

    return "\n".join(sections)
