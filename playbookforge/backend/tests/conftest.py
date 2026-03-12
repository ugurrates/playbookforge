"""Shared test fixtures for PlaybookForge tests."""

import json
import os
from pathlib import Path

import pytest

from backend.core.builder import PlaybookBuilder
from backend.core.cacao_model import (
    CacaoPlaybook,
    Command,
    CommandType,
    PlaybookActivityType,
    PlaybookType,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_playbook_json() -> str:
    """Load the sample phishing playbook JSON fixture."""
    path = FIXTURES_DIR / "sample_phishing_playbook.json"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def sample_playbook(sample_playbook_json: str) -> CacaoPlaybook:
    """Parse the sample phishing playbook fixture into a CacaoPlaybook."""
    return CacaoPlaybook.from_json(sample_playbook_json)


@pytest.fixture
def sample_playbook_dict(sample_playbook_json: str) -> dict:
    """Load the sample phishing playbook as a dict."""
    return json.loads(sample_playbook_json)


@pytest.fixture
def minimal_playbook() -> CacaoPlaybook:
    """Create a minimal valid playbook for testing."""
    return (
        PlaybookBuilder("Minimal Test Playbook")
        .set_description("A minimal playbook for testing")
        .add_type(PlaybookType.INVESTIGATION)
        .add_action_step(
            name="Test Action",
            description="A test action step",
            commands=[
                Command(type=CommandType.HTTP_API, command="GET /api/test")
            ],
        )
        .build()
    )
