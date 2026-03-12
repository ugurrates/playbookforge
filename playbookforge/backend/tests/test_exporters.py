"""Tests for all SOAR platform exporters."""

import json

import yaml
import pytest

from backend.core.cacao_model import CacaoPlaybook
from backend.exporters import registry as exporter_registry
from backend.exporters.base import BaseExporter
from backend.exporters.xsoar_exporter import XSOARExporter
from backend.exporters.shuffle_exporter import ShuffleExporter
from backend.exporters.sentinel_fortisoar_exporter import SentinelExporter, FortiSOARExporter


# ── Registry ─────────────────────────────────────────────────────────

class TestExporterRegistry:
    def test_list_platforms(self):
        platforms = exporter_registry.list_platforms()
        assert len(platforms) == 6
        ids = {p["platform_id"] for p in platforms}
        assert ids == {"xsoar", "shuffle", "sentinel", "fortisoar", "splunk_soar", "google_secops"}

    def test_get_exporter(self):
        assert exporter_registry.get("xsoar") is not None
        assert exporter_registry.get("nonexistent") is None

    def test_export_method(self, sample_playbook: CacaoPlaybook):
        content = exporter_registry.export(sample_playbook, "shuffle")
        assert len(content) > 0

    def test_export_unknown_raises(self, sample_playbook: CacaoPlaybook):
        with pytest.raises(ValueError, match="Unknown platform"):
            exporter_registry.export(sample_playbook, "nonexistent")

    def test_export_all(self, sample_playbook: CacaoPlaybook):
        results = exporter_registry.export_all(sample_playbook)
        assert len(results) == 6
        for pid, content in results.items():
            assert not content.startswith("ERROR")


# ── Base Exporter ────────────────────────────────────────────────────

class TestBaseExporter:
    def test_get_filename(self, sample_playbook: CacaoPlaybook):
        exporter = XSOARExporter()
        filename = exporter.get_filename(sample_playbook)
        assert filename.endswith(".yml")
        assert "phishing" in filename.lower()

    def test_get_metadata(self):
        exporter = XSOARExporter()
        meta = exporter.get_metadata()
        assert meta["platform_id"] == "xsoar"
        assert meta["platform_name"] == "Palo Alto Cortex XSOAR"
        assert meta["file_extension"] == ".yml"


# ── XSOAR Exporter ──────────────────────────────────────────────────

class TestXSOARExporter:
    def test_export_produces_valid_yaml(self, sample_playbook: CacaoPlaybook):
        exporter = XSOARExporter()
        content = exporter.export(sample_playbook)
        data = yaml.safe_load(content)
        assert isinstance(data, dict)

    def test_xsoar_structure(self, sample_playbook: CacaoPlaybook):
        exporter = XSOARExporter()
        data = exporter.export_to_dict(sample_playbook)
        assert "tasks" in data
        assert "starttaskid" in data
        assert "name" in data
        assert "inputs" in data
        assert "outputs" in data
        assert data["name"] == "Phishing Email Investigation & Response"

    def test_xsoar_tasks_have_nexttasks(self, sample_playbook: CacaoPlaybook):
        exporter = XSOARExporter()
        data = exporter.export_to_dict(sample_playbook)
        for tid, task in data["tasks"].items():
            assert "nexttasks" in task
            assert "task" in task
            assert "type" in task

    def test_xsoar_condition_has_conditions(self, sample_playbook: CacaoPlaybook):
        exporter = XSOARExporter()
        data = exporter.export_to_dict(sample_playbook)
        condition_tasks = [t for t in data["tasks"].values() if t["type"] == "condition"]
        assert len(condition_tasks) > 0
        for ct in condition_tasks:
            assert "conditions" in ct

    def test_xsoar_inputs_from_external_vars(self, sample_playbook: CacaoPlaybook):
        exporter = XSOARExporter()
        data = exporter.export_to_dict(sample_playbook)
        assert len(data["inputs"]) > 0
        # email_id is external
        keys = [inp["key"] for inp in data["inputs"]]
        assert "email_id" in keys

    def test_xsoar_tags(self, sample_playbook: CacaoPlaybook):
        exporter = XSOARExporter()
        data = exporter.export_to_dict(sample_playbook)
        assert "phishing" in data["tags"]


# ── Shuffle Exporter ─────────────────────────────────────────────────

class TestShuffleExporter:
    def test_export_produces_valid_json(self, sample_playbook: CacaoPlaybook):
        exporter = ShuffleExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_shuffle_structure(self, sample_playbook: CacaoPlaybook):
        exporter = ShuffleExporter()
        data = exporter.export_to_dict(sample_playbook)
        assert "actions" in data
        assert "triggers" in data
        assert "branches" in data
        assert "workflow_variables" in data
        assert data["name"] == "Phishing Email Investigation & Response"

    def test_shuffle_has_trigger(self, sample_playbook: CacaoPlaybook):
        exporter = ShuffleExporter()
        data = exporter.export_to_dict(sample_playbook)
        assert len(data["triggers"]) >= 1
        trigger = data["triggers"][0]
        assert trigger["trigger_type"] == "WEBHOOK"

    def test_shuffle_branches_connect_actions(self, sample_playbook: CacaoPlaybook):
        exporter = ShuffleExporter()
        data = exporter.export_to_dict(sample_playbook)
        assert len(data["branches"]) > 0
        for branch in data["branches"]:
            assert "source_id" in branch
            assert "destination_id" in branch

    def test_shuffle_variables(self, sample_playbook: CacaoPlaybook):
        exporter = ShuffleExporter()
        data = exporter.export_to_dict(sample_playbook)
        var_names = {v["name"] for v in data["workflow_variables"]}
        assert "email_id" in var_names

    def test_shuffle_metadata(self, sample_playbook: CacaoPlaybook):
        exporter = ShuffleExporter()
        data = exporter.export_to_dict(sample_playbook)
        assert data["_playbookforge_metadata"]["source_format"] == "cacao-2.0"
        assert data["_playbookforge_metadata"]["converter"] == "PlaybookForge"


# ── Sentinel Exporter ────────────────────────────────────────────────

class TestSentinelExporter:
    def test_export_produces_valid_json(self, sample_playbook: CacaoPlaybook):
        exporter = SentinelExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_sentinel_arm_schema(self, sample_playbook: CacaoPlaybook):
        exporter = SentinelExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        assert data["$schema"] == "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#"
        assert data["contentVersion"] == "1.0.0.0"

    def test_sentinel_has_logic_app_resource(self, sample_playbook: CacaoPlaybook):
        exporter = SentinelExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        assert len(data["resources"]) >= 1
        resource = data["resources"][0]
        assert resource["type"] == "Microsoft.Logic/workflows"
        assert resource["apiVersion"] == "2017-07-01"

    def test_sentinel_has_actions(self, sample_playbook: CacaoPlaybook):
        exporter = SentinelExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        definition = data["resources"][0]["properties"]["definition"]
        assert "actions" in definition
        assert len(definition["actions"]) > 0

    def test_sentinel_has_trigger(self, sample_playbook: CacaoPlaybook):
        exporter = SentinelExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        triggers = data["resources"][0]["properties"]["definition"]["triggers"]
        assert "Microsoft_Sentinel_incident" in triggers

    def test_sentinel_parameters_from_external_vars(self, sample_playbook: CacaoPlaybook):
        exporter = SentinelExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        params = data["parameters"]
        assert "PlaybookName" in params
        # email_id is external
        assert "email_id" in params

    def test_sentinel_metadata(self, sample_playbook: CacaoPlaybook):
        exporter = SentinelExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        assert data["metadata"]["_playbookforge"]["source_format"] == "cacao-2.0"


# ── FortiSOAR Exporter ───────────────────────────────────────────────

class TestFortiSOARExporter:
    def test_export_produces_valid_json(self, sample_playbook: CacaoPlaybook):
        exporter = FortiSOARExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        assert isinstance(data, dict)

    def test_fortisoar_structure(self, sample_playbook: CacaoPlaybook):
        exporter = FortiSOARExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        assert data["type"] == "workflow_collections"
        assert "data" in data
        assert len(data["data"]) >= 1

    def test_fortisoar_has_workflows(self, sample_playbook: CacaoPlaybook):
        exporter = FortiSOARExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        collection = data["data"][0]
        assert collection["@type"] == "WorkflowCollection"
        assert len(collection["workflows"]) >= 1

    def test_fortisoar_steps_and_routes(self, sample_playbook: CacaoPlaybook):
        exporter = FortiSOARExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        workflow = data["data"][0]["workflows"][0]
        assert "steps" in workflow
        assert "routes" in workflow
        assert len(workflow["steps"]) > 0
        assert len(workflow["routes"]) > 0

    def test_fortisoar_step_types(self, sample_playbook: CacaoPlaybook):
        exporter = FortiSOARExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        steps = data["data"][0]["workflows"][0]["steps"]
        step_types = {s["stepType"] for s in steps}
        assert any("startStep" in st for st in step_types)
        assert any("endStep" in st for st in step_types)
        assert any("executeStep" in st for st in step_types)

    def test_fortisoar_trigger_step(self, sample_playbook: CacaoPlaybook):
        exporter = FortiSOARExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        workflow = data["data"][0]["workflows"][0]
        assert workflow["triggerStep"] != ""

    def test_fortisoar_metadata(self, sample_playbook: CacaoPlaybook):
        exporter = FortiSOARExporter()
        content = exporter.export(sample_playbook)
        data = json.loads(content)
        workflow = data["data"][0]["workflows"][0]
        assert workflow["_playbookforge_metadata"]["converter"] == "PlaybookForge"


# ── Minimal Playbook Export ──────────────────────────────────────────

class TestMinimalExport:
    """Ensure all exporters handle the simplest possible playbook."""

    @pytest.mark.parametrize("platform_id", ["xsoar", "shuffle", "sentinel", "fortisoar"])
    def test_export_minimal(self, minimal_playbook: CacaoPlaybook, platform_id: str):
        exporter = exporter_registry.get(platform_id)
        content = exporter.export(minimal_playbook)
        assert len(content) > 0
