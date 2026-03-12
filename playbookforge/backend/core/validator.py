"""
PlaybookForge - CACAO v2.0 Playbook Validator
Validates playbooks against OASIS CACAO v2.0 JSON Schema and logical integrity rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .cacao_model import CacaoPlaybook, WorkflowStepType


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    severity: Severity
    code: str
    message: str
    path: str = ""

    def __str__(self) -> str:
        prefix = f"[{self.severity.value.upper()}]"
        loc = f" at {self.path}" if self.path else ""
        return f"{prefix} {self.code}: {self.message}{loc}"


@dataclass
class ValidationResult:
    valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)
    playbook_summary: dict[str, Any] = field(default_factory=dict)

    def add_error(self, code: str, message: str, path: str = "") -> None:
        self.issues.append(ValidationIssue(Severity.ERROR, code, message, path))
        self.valid = False

    def add_warning(self, code: str, message: str, path: str = "") -> None:
        self.issues.append(ValidationIssue(Severity.WARNING, code, message, path))

    def add_info(self, code: str, message: str, path: str = "") -> None:
        self.issues.append(ValidationIssue(Severity.INFO, code, message, path))

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [
                {
                    "severity": i.severity.value,
                    "code": i.code,
                    "message": i.message,
                    "path": i.path,
                }
                for i in self.issues
            ],
            "playbook_summary": self.playbook_summary,
        }


class CacaoValidator:
    """
    Validates CACAO v2.0 playbooks.
    
    Three levels of validation:
    1. Schema validation (Pydantic model parsing)
    2. Structural validation (workflow integrity)
    3. Semantic validation (best practices / quality)
    """

    def validate(self, playbook: CacaoPlaybook) -> ValidationResult:
        """Run all validation checks on a playbook"""
        result = ValidationResult()
        result.playbook_summary = playbook.summary()

        self._validate_metadata(playbook, result)
        self._validate_workflow_structure(playbook, result)
        self._validate_workflow_reachability(playbook, result)
        self._validate_steps(playbook, result)
        self._validate_variables(playbook, result)
        self._validate_agents_targets(playbook, result)
        self._quality_checks(playbook, result)

        return result

    @classmethod
    def validate_json(cls, json_str: str) -> ValidationResult:
        """Validate a CACAO JSON string - includes schema parsing"""
        result = ValidationResult()
        try:
            playbook = CacaoPlaybook.from_json(json_str)
        except Exception as e:
            result.add_error("SCHEMA_PARSE_ERROR", f"Failed to parse CACAO JSON: {str(e)}")
            return result

        validator = cls()
        return validator.validate(playbook)

    # ── Metadata Validation ──────────────────────────────────────────────

    def _validate_metadata(self, pb: CacaoPlaybook, result: ValidationResult) -> None:
        if pb.type != "playbook":
            result.add_error("META_001", "type must be 'playbook'", "type")

        if pb.spec_version != "cacao-2.0":
            result.add_error("META_002", "spec_version must be 'cacao-2.0'", "spec_version")

        if not pb.id.startswith("playbook--"):
            result.add_error("META_003", "id must start with 'playbook--'", "id")

        if not pb.name or len(pb.name.strip()) == 0:
            result.add_error("META_004", "name is required and cannot be empty", "name")

        if not pb.playbook_types:
            result.add_warning("META_005", "playbook_types SHOULD be populated", "playbook_types")

        if not pb.description:
            result.add_warning("META_006", "description SHOULD be populated", "description")

        if not pb.created_by:
            result.add_warning("META_007", "created_by SHOULD be populated", "created_by")

        # Timestamp ordering
        if pb.valid_from and pb.valid_until:
            if pb.valid_from >= pb.valid_until:
                result.add_error("META_008", "valid_until must be greater than valid_from")

    # ── Workflow Structure ───────────────────────────────────────────────

    def _validate_workflow_structure(self, pb: CacaoPlaybook, result: ValidationResult) -> None:
        if not pb.workflow:
            result.add_error("WF_001", "workflow must contain at least one step", "workflow")
            return

        if pb.workflow_start not in pb.workflow:
            result.add_error("WF_002", f"workflow_start '{pb.workflow_start}' not in workflow", "workflow_start")
            return

        start_step = pb.workflow[pb.workflow_start]
        if start_step.type != WorkflowStepType.START:
            result.add_error("WF_003", "workflow_start must point to a 'start' step")

        # Check for end step existence
        has_end = any(s.type == WorkflowStepType.END for s in pb.workflow.values())
        if not has_end:
            result.add_warning("WF_004", "Workflow has no 'end' step")

        # Validate all step ID formats
        for step_id in pb.workflow:
            parts = step_id.split("--")
            if len(parts) != 2:
                result.add_warning("WF_005", f"Step ID '{step_id}' should follow 'type--uuid' format")

    # ── Reachability Check ───────────────────────────────────────────────

    def _validate_workflow_reachability(self, pb: CacaoPlaybook, result: ValidationResult) -> None:
        """Check that all steps are reachable from the start step"""
        if not pb.workflow or pb.workflow_start not in pb.workflow:
            return

        reachable: set[str] = set()
        queue = [pb.workflow_start]

        while queue:
            current = queue.pop(0)
            if current in reachable:
                continue
            reachable.add(current)

            step = pb.workflow.get(current)
            if not step:
                continue

            # Collect all outgoing references
            next_ids = []
            if step.on_completion:
                next_ids.append(step.on_completion)
            if step.on_success:
                next_ids.append(step.on_success)
            if step.on_failure:
                next_ids.append(step.on_failure)
            if step.on_true:
                next_ids.append(step.on_true)
            if step.on_false:
                next_ids.append(step.on_false)
            if step.next_steps:
                next_ids.extend(step.next_steps)
            if step.cases:
                next_ids.extend(step.cases.values())

            for nid in next_ids:
                if nid not in reachable:
                    queue.append(nid)

        unreachable = set(pb.workflow.keys()) - reachable
        for step_id in unreachable:
            result.add_warning(
                "WF_REACH_001",
                f"Step '{step_id}' ({pb.workflow[step_id].name}) is not reachable from start",
                f"workflow.{step_id}",
            )

    # ── Individual Step Validation ───────────────────────────────────────

    def _validate_steps(self, pb: CacaoPlaybook, result: ValidationResult) -> None:
        for step_id, step in pb.workflow.items():
            path = f"workflow.{step_id}"

            # Action steps should have commands or be manual
            if step.type == WorkflowStepType.ACTION:
                if not step.commands:
                    result.add_info(
                        "STEP_001",
                        f"Action step '{step.name}' has no commands (manual step)",
                        path,
                    )

            # Start step must have on_completion
            if step.type == WorkflowStepType.START:
                if not step.on_completion:
                    result.add_error("STEP_002", "Start step must have on_completion", path)

            # End step should not have outgoing refs
            if step.type == WorkflowStepType.END:
                if step.on_completion or step.on_success or step.on_failure:
                    result.add_warning("STEP_003", "End step should not have outgoing references", path)

            # If-condition needs on_true
            if step.type == WorkflowStepType.IF_CONDITION:
                if not step.on_true:
                    result.add_error("STEP_004", "If-condition step must have on_true", path)

            # Dangling steps (no outgoing edge, not end step)
            if step.type not in (WorkflowStepType.END,):
                has_exit = any([
                    step.on_completion, step.on_success, step.on_failure,
                    step.on_true, step.on_false, step.next_steps, step.cases
                ])
                if not has_exit:
                    result.add_warning("STEP_005", f"Step '{step.name}' has no outgoing connection", path)

    # ── Variable Validation ──────────────────────────────────────────────

    def _validate_variables(self, pb: CacaoPlaybook, result: ValidationResult) -> None:
        if not pb.playbook_variables:
            return

        for var_name, var in pb.playbook_variables.items():
            if var.constant and not var.value:
                result.add_warning(
                    "VAR_001",
                    f"Constant variable '{var_name}' has no value",
                    f"playbook_variables.{var_name}",
                )

    # ── Agent/Target Validation ──────────────────────────────────────────

    def _validate_agents_targets(self, pb: CacaoPlaybook, result: ValidationResult) -> None:
        defined_agents = set(pb.agent_definitions.keys()) if pb.agent_definitions else set()
        defined_targets = set(pb.target_definitions.keys()) if pb.target_definitions else set()

        for step_id, step in pb.workflow.items():
            if step.agent and step.agent not in defined_agents:
                result.add_warning(
                    "AT_001",
                    f"Step references agent '{step.agent}' which is not defined",
                    f"workflow.{step_id}.agent",
                )
            if step.targets:
                for t in step.targets:
                    if t not in defined_targets:
                        result.add_warning(
                            "AT_002",
                            f"Step references target '{t}' which is not defined",
                            f"workflow.{step_id}.targets",
                        )

    # ── Quality / Best Practice Checks ───────────────────────────────────

    def _quality_checks(self, pb: CacaoPlaybook, result: ValidationResult) -> None:
        # Naming
        if pb.name and len(pb.name) > 256:
            result.add_warning("QUAL_001", "Playbook name exceeds 256 characters")

        # Step naming
        unnamed_count = 0
        for step in pb.workflow.values():
            if not step.name and step.type not in (WorkflowStepType.START, WorkflowStepType.END):
                unnamed_count += 1
        if unnamed_count > 0:
            result.add_warning("QUAL_002", f"{unnamed_count} step(s) have no name")

        # Description completeness
        undescribed_actions = sum(
            1 for s in pb.workflow.values()
            if s.type == WorkflowStepType.ACTION and not s.description
        )
        if undescribed_actions > 0:
            result.add_info("QUAL_003", f"{undescribed_actions} action step(s) have no description")

        # MITRE ATT&CK references
        has_mitre = False
        if pb.external_references:
            has_mitre = any(
                "mitre" in str(ref).lower() or "attack" in str(ref).lower()
                for ref in pb.external_references
            )
        if not has_mitre:
            result.add_info("QUAL_004", "No MITRE ATT&CK references found — consider adding")

        # Labels
        if not pb.labels:
            result.add_info("QUAL_005", "No labels defined — labels improve searchability")
