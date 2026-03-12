"""Tests for CACAO v2.0 data models."""

import json

import pytest

from backend.core.cacao_model import (
    AgentTarget,
    AgentTargetType,
    AuthenticationInfo,
    CacaoPlaybook,
    Command,
    CommandType,
    PlaybookActivityType,
    PlaybookType,
    Variable,
    WorkflowStep,
    WorkflowStepType,
    generate_cacao_id,
)


# ── ID Generation ────────────────────────────────────────────────────

class TestGenerateCacaoId:
    def test_format(self):
        cid = generate_cacao_id("playbook")
        assert cid.startswith("playbook--")
        parts = cid.split("--")
        assert len(parts) == 2

    def test_uniqueness(self):
        ids = {generate_cacao_id("action") for _ in range(100)}
        assert len(ids) == 100


# ── Enums ────────────────────────────────────────────────────────────

class TestEnums:
    def test_playbook_types(self):
        assert len(PlaybookType) == 7
        assert PlaybookType.INVESTIGATION.value == "investigation"
        assert PlaybookType.ATTACK.value == "attack"

    def test_workflow_step_types(self):
        assert len(WorkflowStepType) == 8
        assert WorkflowStepType.ACTION.value == "action"
        assert WorkflowStepType.IF_CONDITION.value == "if-condition"
        assert WorkflowStepType.PARALLEL.value == "parallel"

    def test_command_types(self):
        assert len(CommandType) == 12
        assert CommandType.HTTP_API.value == "http-api"
        assert CommandType.BASH.value == "bash"

    def test_agent_target_types(self):
        assert len(AgentTargetType) == 11
        assert AgentTargetType.HTTP_API.value == "http-api"

    def test_playbook_activity_types(self):
        assert len(PlaybookActivityType) == 20
        assert PlaybookActivityType.SCAN_SYSTEM.value == "scan-system"


# ── Variable Model ───────────────────────────────────────────────────

class TestVariable:
    def test_basic(self):
        v = Variable(type="string", value="hello")
        assert v.type == "string"
        assert v.value == "hello"
        assert v.constant is False
        assert v.external is False

    def test_constant_external(self):
        v = Variable(type="integer", constant=True, external=True, value="42")
        assert v.constant is True
        assert v.external is True


# ── Command Model ────────────────────────────────────────────────────

class TestCommand:
    def test_valid_command(self):
        cmd = Command(type=CommandType.HTTP_API, command="GET /api/test")
        assert cmd.type == CommandType.HTTP_API
        assert cmd.command == "GET /api/test"

    def test_command_b64(self):
        cmd = Command(type=CommandType.BASH, command_b64="ZWNobyBoZWxsbw==")
        assert cmd.command_b64 is not None

    def test_missing_command_raises(self):
        with pytest.raises(ValueError, match="command.*command_b64"):
            Command(type=CommandType.BASH)


# ── WorkflowStep Model ──────────────────────────────────────────────

class TestWorkflowStep:
    def test_action_step(self):
        step = WorkflowStep(
            type=WorkflowStepType.ACTION,
            name="Test",
            commands=[Command(type=CommandType.HTTP_API, command="GET /")],
        )
        assert step.type == WorkflowStepType.ACTION
        assert step.name == "Test"

    def test_if_condition_requires_condition(self):
        with pytest.raises(ValueError, match="condition"):
            WorkflowStep(type=WorkflowStepType.IF_CONDITION, name="Bad")

    def test_if_condition_valid(self):
        step = WorkflowStep(
            type=WorkflowStepType.IF_CONDITION,
            name="Check",
            condition="x == true",
            on_true="step--1",
        )
        assert step.condition == "x == true"

    def test_parallel_requires_next_steps(self):
        with pytest.raises(ValueError, match="next_steps"):
            WorkflowStep(type=WorkflowStepType.PARALLEL, name="Bad")

    def test_parallel_valid(self):
        step = WorkflowStep(
            type=WorkflowStepType.PARALLEL,
            name="Fork",
            next_steps=["step--a", "step--b"],
        )
        assert len(step.next_steps) == 2

    def test_start_step(self):
        step = WorkflowStep(type=WorkflowStepType.START, name="Start")
        assert step.type == WorkflowStepType.START

    def test_end_step(self):
        step = WorkflowStep(type=WorkflowStepType.END, name="End")
        assert step.type == WorkflowStepType.END


# ── CacaoPlaybook Model ─────────────────────────────────────────────

class TestCacaoPlaybook:
    def test_create_minimal(self, minimal_playbook: CacaoPlaybook):
        assert minimal_playbook.name == "Minimal Test Playbook"
        assert minimal_playbook.spec_version == "cacao-2.0"
        assert minimal_playbook.type == "playbook"
        assert minimal_playbook.id.startswith("playbook--")

    def test_workflow_start_must_exist(self):
        with pytest.raises(ValueError, match="workflow_start"):
            CacaoPlaybook(
                name="Bad",
                workflow_start="nonexistent",
                workflow={},
            )

    def test_workflow_start_must_be_start_type(self):
        with pytest.raises(ValueError, match="start"):
            CacaoPlaybook(
                name="Bad",
                workflow_start="action--1",
                workflow={
                    "action--1": WorkflowStep(
                        type=WorkflowStepType.ACTION,
                        name="Not Start",
                        commands=[Command(type=CommandType.HTTP_API, command="GET /")],
                    )
                },
            )

    def test_dangling_reference_raises(self):
        with pytest.raises(ValueError, match="does not exist"):
            CacaoPlaybook(
                name="Bad",
                workflow_start="start--1",
                workflow={
                    "start--1": WorkflowStep(
                        type=WorkflowStepType.START,
                        name="Start",
                        on_completion="nonexistent--id",
                    ),
                },
            )

    def test_serialization_roundtrip(self, sample_playbook: CacaoPlaybook):
        json_str = sample_playbook.to_json()
        restored = CacaoPlaybook.from_json(json_str)
        assert restored.name == sample_playbook.name
        assert restored.id == sample_playbook.id
        assert len(restored.workflow) == len(sample_playbook.workflow)

    def test_to_json_exclude_none(self, minimal_playbook: CacaoPlaybook):
        json_str = minimal_playbook.to_json(exclude_none=True)
        data = json.loads(json_str)
        assert "playbook_activities" not in data

    def test_get_steps_in_order(self, sample_playbook: CacaoPlaybook):
        ordered = sample_playbook.get_steps_in_order()
        assert len(ordered) > 0
        assert ordered[0][1].type == WorkflowStepType.START

    def test_get_action_steps(self, sample_playbook: CacaoPlaybook):
        actions = sample_playbook.get_action_steps()
        assert len(actions) > 0
        for _, step in actions:
            assert step.type == WorkflowStepType.ACTION

    def test_summary(self, sample_playbook: CacaoPlaybook):
        summary = sample_playbook.summary()
        assert summary["name"] == "Phishing Email Investigation & Response"
        assert summary["total_steps"] == 12
        assert "action" in summary["step_types"]

    def test_add_step(self, minimal_playbook: CacaoPlaybook):
        new_id = minimal_playbook.add_step(
            WorkflowStepType.ACTION,
            "Dynamic Step",
            commands=[Command(type=CommandType.BASH, command="echo hello")],
        )
        assert new_id in minimal_playbook.workflow


# ── AgentTarget & AuthenticationInfo ─────────────────────────────────

class TestAgentTarget:
    def test_create(self):
        agent = AgentTarget(type=AgentTargetType.HTTP_API, name="Test API")
        assert agent.name == "Test API"


class TestAuthenticationInfo:
    def test_create(self):
        auth = AuthenticationInfo(type="http-basic", username="user", password="pass")
        assert auth.type == "http-basic"
        assert auth.kms is False
