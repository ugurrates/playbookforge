"""Tests for CACAO v2.0 PlaybookBuilder fluent API."""

import pytest

from backend.core.builder import PlaybookBuilder
from backend.core.cacao_model import (
    AgentTargetType,
    CacaoPlaybook,
    Command,
    CommandType,
    PlaybookActivityType,
    PlaybookType,
    WorkflowStepType,
)
from backend.core.validator import CacaoValidator


# ── Basic Builder ────────────────────────────────────────────────────

class TestBuilderBasic:
    def test_minimal_build(self):
        pb = (
            PlaybookBuilder("Test")
            .add_action_step(
                name="Step 1",
                commands=[Command(type=CommandType.HTTP_API, command="GET /")],
            )
            .build()
        )
        assert isinstance(pb, CacaoPlaybook)
        assert pb.name == "Test"
        # start + 1 action + end = 3
        assert len(pb.workflow) == 3

    def test_built_playbook_validates(self):
        pb = (
            PlaybookBuilder("Valid Playbook")
            .set_description("Test")
            .add_type(PlaybookType.INVESTIGATION)
            .add_action_step(
                name="Action",
                commands=[Command(type=CommandType.HTTP_API, command="GET /")],
            )
            .build()
        )
        result = CacaoValidator().validate(pb)
        assert result.valid is True


# ── Metadata Methods ─────────────────────────────────────────────────

class TestBuilderMetadata:
    def test_set_description(self):
        pb = (
            PlaybookBuilder("Test")
            .set_description("A description")
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert pb.description == "A description"

    def test_add_types(self):
        pb = (
            PlaybookBuilder("Test")
            .add_type(PlaybookType.INVESTIGATION)
            .add_type(PlaybookType.REMEDIATION)
            .add_type(PlaybookType.INVESTIGATION)  # duplicate should be ignored
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert len(pb.playbook_types) == 2

    def test_add_activities(self):
        pb = (
            PlaybookBuilder("Test")
            .add_activity(PlaybookActivityType.SCAN_SYSTEM)
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert PlaybookActivityType.SCAN_SYSTEM in pb.playbook_activities

    def test_add_labels(self):
        pb = (
            PlaybookBuilder("Test")
            .add_label("phishing")
            .add_label("email")
            .add_label("phishing")  # duplicate
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert pb.labels == ["phishing", "email"]

    def test_set_priority_severity_impact(self):
        pb = (
            PlaybookBuilder("Test")
            .set_priority(1)
            .set_severity(80)
            .set_impact(50)
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert pb.priority == 1
        assert pb.severity == 80
        assert pb.impact == 50

    def test_set_created_by(self):
        pb = (
            PlaybookBuilder("Test")
            .set_created_by("identity--custom-id")
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert pb.created_by == "identity--custom-id"

    def test_add_industry_sector(self):
        pb = (
            PlaybookBuilder("Test")
            .add_industry_sector("finance")
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert "finance" in pb.industry_sectors

    def test_add_mitre_reference(self):
        pb = (
            PlaybookBuilder("Test")
            .add_mitre_reference("T1566.001", "Spearphishing Attachment")
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert len(pb.external_references) == 1
        ref = pb.external_references[0]
        assert "MITRE" in ref["name"]
        assert "T1566" in ref["url"]

    def test_add_external_reference(self):
        pb = (
            PlaybookBuilder("Test")
            .add_external_reference("Test Ref", "https://example.com", "A reference")
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert pb.external_references[0]["name"] == "Test Ref"


# ── Variables ────────────────────────────────────────────────────────

class TestBuilderVariables:
    def test_add_variable(self):
        pb = (
            PlaybookBuilder("Test")
            .add_variable("email_id", var_type="string", external=True, description="Email ID")
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        assert "email_id" in pb.playbook_variables
        v = pb.playbook_variables["email_id"]
        assert v.external is True
        assert v.type == "string"


# ── Agents & Targets ────────────────────────────────────────────────

class TestBuilderAgentsTargets:
    def test_add_agent(self):
        builder = PlaybookBuilder("Test")
        agent_id = builder.add_agent("SOC Team", AgentTargetType.ORGANIZATION)
        assert agent_id.startswith("organization--")
        pb = builder.add_action_step(
            name="A",
            commands=[Command(type=CommandType.HTTP_API, command="GET /")],
        ).build()
        assert agent_id in pb.agent_definitions

    def test_add_target(self):
        builder = PlaybookBuilder("Test")
        target_id = builder.add_target("Email Gateway", AgentTargetType.HTTP_API)
        assert target_id.startswith("http-api--")
        pb = builder.add_action_step(
            name="A",
            commands=[Command(type=CommandType.HTTP_API, command="GET /")],
        ).build()
        assert target_id in pb.target_definitions


# ── Workflow Steps ───────────────────────────────────────────────────

class TestBuilderSteps:
    def test_action_step(self):
        pb = (
            PlaybookBuilder("Test")
            .add_action_step(
                name="My Action",
                description="Does something",
                commands=[Command(type=CommandType.HTTP_API, command="GET /api")],
            )
            .build()
        )
        action_steps = [s for s in pb.workflow.values() if s.type == WorkflowStepType.ACTION]
        assert len(action_steps) == 1
        assert action_steps[0].name == "My Action"

    def test_manual_step(self):
        pb = (
            PlaybookBuilder("Test")
            .add_manual_step("Manual Task", "Do this manually")
            .build()
        )
        action_steps = [s for s in pb.workflow.values() if s.type == WorkflowStepType.ACTION]
        assert len(action_steps) == 1
        assert action_steps[0].commands[0].type == CommandType.MANUAL

    def test_if_condition(self):
        pb = (
            PlaybookBuilder("Test")
            .add_action_step(name="Before", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .add_if_condition(
                name="Check",
                condition="x == true",
                on_true_name="Before",
                on_false_name="After",
            )
            .add_action_step(name="After", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .build()
        )
        cond_steps = [s for s in pb.workflow.values() if s.type == WorkflowStepType.IF_CONDITION]
        assert len(cond_steps) == 1
        assert cond_steps[0].condition == "x == true"
        assert cond_steps[0].on_true is not None
        assert cond_steps[0].on_false is not None

    def test_parallel_steps(self):
        pb = (
            PlaybookBuilder("Test")
            .add_action_step(name="A", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .add_action_step(name="B", commands=[Command(type=CommandType.HTTP_API, command="GET /")])
            .add_parallel_steps("Fork", parallel_step_names=["A", "B"])
            .build()
        )
        par_steps = [s for s in pb.workflow.values() if s.type == WorkflowStepType.PARALLEL]
        assert len(par_steps) == 1
        assert len(par_steps[0].next_steps) == 2

    def test_playbook_action(self):
        pb = (
            PlaybookBuilder("Test")
            .add_playbook_action(
                name="Run Sub-Playbook",
                playbook_id="playbook--sub-123",
                description="Execute child playbook",
            )
            .build()
        )
        pa_steps = [s for s in pb.workflow.values() if s.type == WorkflowStepType.PLAYBOOK_ACTION]
        assert len(pa_steps) == 1
        assert pa_steps[0].playbook_id == "playbook--sub-123"

    def test_step_chaining(self):
        pb = (
            PlaybookBuilder("Test")
            .add_action_step(name="Step 1", commands=[Command(type=CommandType.HTTP_API, command="GET /1")])
            .add_action_step(name="Step 2", commands=[Command(type=CommandType.HTTP_API, command="GET /2")])
            .add_action_step(name="Step 3", commands=[Command(type=CommandType.HTTP_API, command="GET /3")])
            .build()
        )
        # start + 3 actions + end = 5
        assert len(pb.workflow) == 5
        # Verify linear chaining
        ordered = pb.get_steps_in_order()
        names = [s.name for _, s in ordered if s.type == WorkflowStepType.ACTION]
        assert names == ["Step 1", "Step 2", "Step 3"]


# ── Full Pipeline (Build + Validate) ────────────────────────────────

class TestBuilderFullPipeline:
    def test_sample_playbook_roundtrip(self, sample_playbook: CacaoPlaybook):
        """The sample fixture should validate cleanly."""
        result = CacaoValidator().validate(sample_playbook)
        assert result.valid is True
        assert result.playbook_summary["total_steps"] == 12
