"""Tests for CACAO v2.0 playbook validator."""

import json

import pytest

from backend.core.cacao_model import (
    CacaoPlaybook,
    Command,
    CommandType,
    PlaybookType,
    Variable,
    WorkflowStep,
    WorkflowStepType,
    generate_cacao_id,
)
from backend.core.validator import CacaoValidator, Severity, ValidationResult


@pytest.fixture
def validator() -> CacaoValidator:
    return CacaoValidator()


# ── Valid playbook passes ────────────────────────────────────────────

class TestValidPlaybook:
    def test_sample_playbook_is_valid(self, validator: CacaoValidator, sample_playbook: CacaoPlaybook):
        result = validator.validate(sample_playbook)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_minimal_playbook_is_valid(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        result = validator.validate(minimal_playbook)
        assert result.valid is True


# ── Metadata validation ──────────────────────────────────────────────

class TestMetadataValidation:
    def test_meta_001_wrong_type(self, validator: CacaoValidator, sample_playbook: CacaoPlaybook):
        sample_playbook.type = "not-playbook"
        result = validator.validate(sample_playbook)
        assert any(i.code == "META_001" for i in result.issues)
        assert result.valid is False

    def test_meta_002_wrong_spec_version(self, validator: CacaoValidator, sample_playbook: CacaoPlaybook):
        sample_playbook.spec_version = "cacao-1.0"
        result = validator.validate(sample_playbook)
        assert any(i.code == "META_002" for i in result.issues)

    def test_meta_003_bad_id_prefix(self, validator: CacaoValidator, sample_playbook: CacaoPlaybook):
        sample_playbook.id = "bad-id-format"
        result = validator.validate(sample_playbook)
        assert any(i.code == "META_003" for i in result.issues)

    def test_meta_004_empty_name(self, validator: CacaoValidator, sample_playbook: CacaoPlaybook):
        sample_playbook.name = ""
        result = validator.validate(sample_playbook)
        assert any(i.code == "META_004" for i in result.issues)

    def test_meta_005_no_types_warning(self, validator: CacaoValidator, sample_playbook: CacaoPlaybook):
        sample_playbook.playbook_types = []
        result = validator.validate(sample_playbook)
        assert any(i.code == "META_005" for i in result.issues)

    def test_meta_006_no_description_warning(self, validator: CacaoValidator, sample_playbook: CacaoPlaybook):
        sample_playbook.description = None
        result = validator.validate(sample_playbook)
        assert any(i.code == "META_006" for i in result.issues)

    def test_meta_008_invalid_validity_range(self, validator: CacaoValidator, sample_playbook: CacaoPlaybook):
        sample_playbook.valid_from = "2025-01-01T00:00:00Z"
        sample_playbook.valid_until = "2024-01-01T00:00:00Z"
        result = validator.validate(sample_playbook)
        assert any(i.code == "META_008" for i in result.issues)


# ── Workflow structure ───────────────────────────────────────────────

class TestWorkflowStructure:
    def test_wf_004_no_end_step(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        # Remove end steps
        end_ids = [sid for sid, s in minimal_playbook.workflow.items() if s.type == WorkflowStepType.END]
        for eid in end_ids:
            del minimal_playbook.workflow[eid]
        # Fix references pointing to removed end steps
        for step in minimal_playbook.workflow.values():
            if step.on_completion in end_ids:
                step.on_completion = None
        result = validator.validate(minimal_playbook)
        assert any(i.code == "WF_004" for i in result.issues)

    def test_wf_005_bad_step_id_format(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        # Add a step with bad ID format
        minimal_playbook.workflow["bad_id_no_dashes"] = WorkflowStep(
            type=WorkflowStepType.ACTION,
            name="Bad ID",
            commands=[Command(type=CommandType.HTTP_API, command="GET /")],
        )
        result = validator.validate(minimal_playbook)
        assert any(i.code == "WF_005" for i in result.issues)


# ── Reachability ─────────────────────────────────────────────────────

class TestReachability:
    def test_unreachable_step_warning(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        # Add an orphan step
        orphan_id = generate_cacao_id("action")
        minimal_playbook.workflow[orphan_id] = WorkflowStep(
            type=WorkflowStepType.ACTION,
            name="Orphan",
            commands=[Command(type=CommandType.HTTP_API, command="GET /")],
        )
        result = validator.validate(minimal_playbook)
        assert any(i.code == "WF_REACH_001" for i in result.issues)


# ── Step validation ──────────────────────────────────────────────────

class TestStepValidation:
    def test_step_002_start_no_on_completion(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        start_id = minimal_playbook.workflow_start
        minimal_playbook.workflow[start_id].on_completion = None
        result = validator.validate(minimal_playbook)
        assert any(i.code == "STEP_002" for i in result.issues)

    def test_step_004_if_condition_no_on_true(self, validator: CacaoValidator, sample_playbook: CacaoPlaybook):
        # Find the if-condition step and remove on_true
        for sid, step in sample_playbook.workflow.items():
            if step.type == WorkflowStepType.IF_CONDITION:
                step.on_true = None
                break
        result = validator.validate(sample_playbook)
        assert any(i.code == "STEP_004" for i in result.issues)


# ── Variable validation ──────────────────────────────────────────────

class TestVariableValidation:
    def test_var_001_constant_no_value(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        minimal_playbook.playbook_variables = {
            "test_var": Variable(type="string", constant=True, value=None),
        }
        result = validator.validate(minimal_playbook)
        assert any(i.code == "VAR_001" for i in result.issues)


# ── Agent/Target validation ──────────────────────────────────────────

class TestAgentTargetValidation:
    def test_at_001_undefined_agent(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        for step in minimal_playbook.workflow.values():
            if step.type == WorkflowStepType.ACTION:
                step.agent = "nonexistent--agent"
                break
        result = validator.validate(minimal_playbook)
        assert any(i.code == "AT_001" for i in result.issues)

    def test_at_002_undefined_target(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        for step in minimal_playbook.workflow.values():
            if step.type == WorkflowStepType.ACTION:
                step.targets = ["nonexistent--target"]
                break
        result = validator.validate(minimal_playbook)
        assert any(i.code == "AT_002" for i in result.issues)


# ── Quality checks ───────────────────────────────────────────────────

class TestQualityChecks:
    def test_qual_001_long_name(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        minimal_playbook.name = "x" * 300
        result = validator.validate(minimal_playbook)
        assert any(i.code == "QUAL_001" for i in result.issues)

    def test_qual_004_no_mitre(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        minimal_playbook.external_references = None
        result = validator.validate(minimal_playbook)
        assert any(i.code == "QUAL_004" for i in result.issues)

    def test_qual_005_no_labels(self, validator: CacaoValidator, minimal_playbook: CacaoPlaybook):
        minimal_playbook.labels = None
        result = validator.validate(minimal_playbook)
        assert any(i.code == "QUAL_005" for i in result.issues)


# ── validate_json class method ───────────────────────────────────────

class TestValidateJson:
    def test_valid_json(self, sample_playbook_json: str):
        result = CacaoValidator.validate_json(sample_playbook_json)
        assert result.valid is True

    def test_invalid_json(self):
        result = CacaoValidator.validate_json("{invalid json")
        assert result.valid is False
        assert any(i.code == "SCHEMA_PARSE_ERROR" for i in result.issues)

    def test_malformed_playbook(self):
        result = CacaoValidator.validate_json('{"name": "test"}')
        assert result.valid is False


# ── ValidationResult ─────────────────────────────────────────────────

class TestValidationResult:
    def test_to_dict(self):
        r = ValidationResult()
        r.add_error("E1", "Error msg", "path")
        r.add_warning("W1", "Warning msg")
        r.add_info("I1", "Info msg")
        d = r.to_dict()
        assert d["valid"] is False
        assert d["error_count"] == 1
        assert d["warning_count"] == 1
        assert len(d["issues"]) == 3

    def test_severity_filtering(self):
        r = ValidationResult()
        r.add_error("E1", "err")
        r.add_warning("W1", "warn")
        assert len(r.errors) == 1
        assert len(r.warnings) == 1
