"""Tests for PlaybookForge PDF Generator."""

import pytest
from backend.pdf.generator import pdf_generator


# -- Fixtures --

@pytest.fixture
def sample_playbook():
    """Minimal CACAO playbook dict."""
    return {
        "type": "playbook",
        "spec_version": "cacao-2.0",
        "id": "playbook--test-001",
        "name": "Test Phishing Response",
        "description": "A test playbook for PDF generation.",
        "playbook_types": ["investigation"],
        "created": "2024-01-01T00:00:00Z",
        "modified": "2024-01-02T00:00:00Z",
        "workflow_start": "start--001",
        "workflow": {
            "start--001": {
                "type": "start",
                "name": "Start",
                "on_completion": "action--001",
            },
            "action--001": {
                "type": "action",
                "name": "Extract Indicators",
                "description": "Extract IOCs from the phishing email.",
                "commands": [
                    {
                        "type": "http-api",
                        "command": "POST /api/extract-iocs",
                        "description": "Call IOC extraction service",
                    }
                ],
                "on_completion": "if-condition--001",
            },
            "if-condition--001": {
                "type": "if-condition",
                "name": "Is Malicious?",
                "condition": "malicious_score > 70",
                "on_true": "action--002",
                "on_false": "end--001",
            },
            "action--002": {
                "type": "action",
                "name": "Block IP",
                "description": "Block the attacker IP on firewall.",
                "on_completion": "end--001",
            },
            "end--001": {
                "type": "end",
                "name": "End",
            },
        },
        "playbook_variables": {
            "__email_id__": {
                "type": "string",
                "value": "",
                "description": "ID of the phishing email to investigate",
            },
            "__malicious_score__": {
                "type": "integer",
                "value": "0",
                "description": "Malicious score from analysis",
            },
        },
        "external_references": [
            {"name": "T1566", "url": "https://attack.mitre.org/techniques/T1566/"},
            {"name": "T1204", "url": "https://attack.mitre.org/techniques/T1204/"},
        ],
    }


@pytest.fixture
def validation_result():
    """Sample validation result."""
    return {
        "valid": True,
        "error_count": 0,
        "warning_count": 1,
        "issues": [
            {
                "severity": "warning",
                "code": "QUAL_001",
                "message": "Consider adding more description to steps",
                "path": "workflow.action--002",
            }
        ],
        "playbook_summary": {},
    }


# -- Tests --

class TestPdfGenerator:
    def test_generate_basic_pdf(self, sample_playbook):
        """PDF should be generated and start with %PDF."""
        pdf_bytes = pdf_generator.generate(sample_playbook)
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"
        assert len(pdf_bytes) > 1000

    def test_generate_with_validation(self, sample_playbook, validation_result):
        """PDF with validation report should be larger than without."""
        pdf_without = pdf_generator.generate(sample_playbook)
        pdf_with = pdf_generator.generate(sample_playbook, validation_result)
        assert isinstance(pdf_with, bytes)
        assert pdf_with[:5] == b"%PDF-"
        # With validation should have more content
        assert len(pdf_with) > len(pdf_without)

    def test_minimal_playbook(self):
        """PDF should work with minimal playbook data."""
        minimal = {
            "name": "Minimal",
            "workflow_start": "",
            "workflow": {},
        }
        pdf_bytes = pdf_generator.generate(minimal)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_playbook_with_many_steps(self, sample_playbook):
        """PDF should handle playbooks with many steps."""
        for i in range(20):
            sample_playbook["workflow"][f"action--extra-{i}"] = {
                "type": "action",
                "name": f"Extra Step {i}",
                "description": f"Description for extra step {i}",
                "commands": [{"type": "manual", "command": f"cmd_{i}"}],
            }
        pdf_bytes = pdf_generator.generate(sample_playbook)
        assert pdf_bytes[:5] == b"%PDF-"
        # Should be notably larger due to extra steps
        assert len(pdf_bytes) > 5000

    def test_playbook_with_empty_fields(self):
        """PDF should handle empty/missing optional fields gracefully."""
        playbook = {
            "name": "No Description Playbook",
            "workflow_start": "start--1",
            "workflow": {
                "start--1": {"type": "start", "on_completion": "end--1"},
                "end--1": {"type": "end"},
            },
        }
        pdf_bytes = pdf_generator.generate(playbook)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_special_characters(self):
        """PDF should handle special characters without crashing."""
        playbook = {
            "name": "Test <Special> & 'Characters' \"Playbook\"",
            "description": "Description with <html> & special chars: éàü",
            "workflow_start": "",
            "workflow": {},
        }
        pdf_bytes = pdf_generator.generate(playbook)
        assert pdf_bytes[:5] == b"%PDF-"
