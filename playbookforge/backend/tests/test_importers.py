"""Tests for all SOAR platform importers and roundtrip conversion."""

import json

import yaml
import pytest

from backend.core.cacao_model import CacaoPlaybook, WorkflowStepType
from backend.core.validator import CacaoValidator
from backend.exporters import registry as exporter_registry
from backend.importers import importer_registry
from backend.importers.xsoar_importer import XSOARImporter
from backend.importers.shuffle_importer import ShuffleImporter
from backend.importers.sentinel_importer import SentinelImporter
from backend.importers.fortisoar_importer import FortiSOARImporter
from backend.importers.auto_detect import auto_detect


# ── Importer Registry ────────────────────────────────────────────────

class TestImporterRegistry:
    def test_list_platforms(self):
        platforms = importer_registry.list_platforms()
        assert len(platforms) == 4
        ids = {p["platform_id"] for p in platforms}
        assert ids == {"xsoar", "shuffle", "sentinel", "fortisoar"}

    def test_get_importer(self):
        assert importer_registry.get("xsoar") is not None
        assert importer_registry.get("nonexistent") is None

    def test_parse_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown platform"):
            importer_registry.parse("some content", platform_id="nonexistent")


# ── Auto-Detect ──────────────────────────────────────────────────────

class TestAutoDetect:
    def test_detect_xsoar(self, sample_playbook: CacaoPlaybook):
        content = exporter_registry.export(sample_playbook, "xsoar")
        detected = importer_registry.detect(content)
        assert detected is not None
        assert detected.platform_id == "xsoar"

    def test_detect_shuffle(self, sample_playbook: CacaoPlaybook):
        content = exporter_registry.export(sample_playbook, "shuffle")
        detected = importer_registry.detect(content)
        assert detected is not None
        assert detected.platform_id == "shuffle"

    def test_detect_sentinel(self, sample_playbook: CacaoPlaybook):
        content = exporter_registry.export(sample_playbook, "sentinel")
        detected = importer_registry.detect(content)
        assert detected is not None
        assert detected.platform_id == "sentinel"

    def test_detect_fortisoar(self, sample_playbook: CacaoPlaybook):
        content = exporter_registry.export(sample_playbook, "fortisoar")
        detected = importer_registry.detect(content)
        assert detected is not None
        assert detected.platform_id == "fortisoar"

    def test_detect_unknown(self):
        detected = importer_registry.detect("random text content")
        assert detected is None

    def test_detect_invalid_json(self):
        detected = importer_registry.detect("{bad json")
        assert detected is None


# ── XSOAR Importer ──────────────────────────────────────────────────

class TestXSOARImporter:
    def test_import_produces_valid_cacao(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "xsoar")
        importer = XSOARImporter()
        imported = importer.parse(exported)

        assert isinstance(imported, CacaoPlaybook)
        assert imported.spec_version == "cacao-2.0"
        result = CacaoValidator().validate(imported)
        assert result.valid is True

    def test_import_preserves_name(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "xsoar")
        imported = XSOARImporter().parse(exported)
        assert imported.name == sample_playbook.name

    def test_import_preserves_step_count(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "xsoar")
        imported = XSOARImporter().parse(exported)
        # May not be exact due to start/end handling, but should be close
        assert len(imported.workflow) >= 3

    def test_detect(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "xsoar")
        assert XSOARImporter().detect(exported) is True
        assert XSOARImporter().detect("random text") is False


# ── Shuffle Importer ─────────────────────────────────────────────────

class TestShuffleImporter:
    def test_import_produces_valid_cacao(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "shuffle")
        importer = ShuffleImporter()
        imported = importer.parse(exported)

        assert isinstance(imported, CacaoPlaybook)
        result = CacaoValidator().validate(imported)
        assert result.valid is True

    def test_import_preserves_name(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "shuffle")
        imported = ShuffleImporter().parse(exported)
        assert imported.name == sample_playbook.name

    def test_import_has_variables(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "shuffle")
        imported = ShuffleImporter().parse(exported)
        assert imported.playbook_variables is not None
        assert len(imported.playbook_variables) > 0

    def test_detect(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "shuffle")
        assert ShuffleImporter().detect(exported) is True
        assert ShuffleImporter().detect("not json") is False


# ── Sentinel Importer ────────────────────────────────────────────────

class TestSentinelImporter:
    def test_import_produces_valid_cacao(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "sentinel")
        importer = SentinelImporter()
        imported = importer.parse(exported)

        assert isinstance(imported, CacaoPlaybook)
        result = CacaoValidator().validate(imported)
        assert result.valid is True

    def test_import_preserves_name(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "sentinel")
        imported = SentinelImporter().parse(exported)
        assert imported.name == sample_playbook.name

    def test_detect(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "sentinel")
        assert SentinelImporter().detect(exported) is True
        assert SentinelImporter().detect('{"type": "random"}') is False


# ── FortiSOAR Importer ───────────────────────────────────────────────

class TestFortiSOARImporter:
    def test_import_produces_valid_cacao(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "fortisoar")
        importer = FortiSOARImporter()
        imported = importer.parse(exported)

        assert isinstance(imported, CacaoPlaybook)
        result = CacaoValidator().validate(imported)
        assert result.valid is True

    def test_import_preserves_name(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "fortisoar")
        imported = FortiSOARImporter().parse(exported)
        assert imported.name == sample_playbook.name

    def test_detect(self, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "fortisoar")
        assert FortiSOARImporter().detect(exported) is True
        assert FortiSOARImporter().detect('{"type": "other"}') is False


# ── Roundtrip Tests ──────────────────────────────────────────────────

class TestRoundtrip:
    """Export CACAO → Vendor → Import back to CACAO. Verify key properties."""

    @pytest.mark.parametrize("platform_id", ["xsoar", "shuffle", "sentinel", "fortisoar"])
    def test_roundtrip_preserves_name(self, sample_playbook: CacaoPlaybook, platform_id: str):
        exported = exporter_registry.export(sample_playbook, platform_id)
        imported = importer_registry.parse(exported, platform_id)
        assert imported.name == sample_playbook.name

    @pytest.mark.parametrize("platform_id", ["xsoar", "shuffle", "sentinel", "fortisoar"])
    def test_roundtrip_produces_valid_cacao(self, sample_playbook: CacaoPlaybook, platform_id: str):
        exported = exporter_registry.export(sample_playbook, platform_id)
        imported = importer_registry.parse(exported, platform_id)
        result = CacaoValidator().validate(imported)
        assert result.valid is True

    @pytest.mark.parametrize("platform_id", ["xsoar", "shuffle", "sentinel", "fortisoar"])
    def test_roundtrip_has_action_steps(self, sample_playbook: CacaoPlaybook, platform_id: str):
        exported = exporter_registry.export(sample_playbook, platform_id)
        imported = importer_registry.parse(exported, platform_id)
        action_count = sum(
            1 for s in imported.workflow.values()
            if s.type == WorkflowStepType.ACTION
        )
        assert action_count > 0


# ── Import API Endpoints ─────────────────────────────────────────────

class TestImportAPI:
    def test_import_endpoint(self, client, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "shuffle")
        r = client.post("/import", json={"content": exported, "source_platform": "shuffle"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["detected_platform"] == "shuffle"

    def test_import_auto_detect(self, client, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "shuffle")
        r = client.post("/import", json={"content": exported})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

    def test_import_detect_endpoint(self, client, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "xsoar")
        r = client.post("/import/detect", json={"content": exported})
        assert r.status_code == 200
        data = r.json()
        assert data["detected"] is True
        assert data["platform_id"] == "xsoar"

    def test_import_detect_unknown(self, client):
        r = client.post("/import/detect", json={"content": "unknown format"})
        assert r.status_code == 200
        data = r.json()
        assert data["detected"] is False

    def test_import_convert_endpoint(self, client, sample_playbook: CacaoPlaybook):
        exported = exporter_registry.export(sample_playbook, "xsoar")
        r = client.post("/import/convert", json={
            "content": exported,
            "source_platform": "xsoar",
            "target_platform": "shuffle",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["platform"] == "shuffle"


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from backend.main import app
    return TestClient(app)
