"""
PlaybookForge - CACAO v2.0 Security Playbook Data Models
Based on OASIS CACAO Security Playbooks Version 2.0 CS01 (November 2023)
https://docs.oasis-open.org/cacao/security-playbooks/v2.0/security-playbooks-v2.0.html
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Enums & Vocabularies (Section 3.1, 4.1, 5.1)
# ============================================================================

class PlaybookType(str, Enum):
    NOTIFICATION = "notification"
    DETECTION = "detection"
    INVESTIGATION = "investigation"
    PREVENTION = "prevention"
    MITIGATION = "mitigation"
    REMEDIATION = "remediation"
    ATTACK = "attack"


class PlaybookActivityType(str, Enum):
    COMPOSE_CONTENT = "compose-content"
    DELIVER_CONTENT = "deliver-content"
    IDENTIFY_AUDIENCE = "identify-audience"
    SCAN_SYSTEM = "scan-system"
    ANALYZE_COLLECTED_DATA = "analyze-collected-data"
    IDENTIFY_INDICATORS = "identify-indicators"
    IDENTIFY_IOCS = "identify-iocs"
    MATCH_INDICATORS = "match-indicators"
    INVESTIGATE_SYSTEM = "investigate-system"
    DEPLOY_COUNTERMEASURE = "deploy-countermeasure"
    CONTAIN_SYSTEM = "contain-system"
    DIVERT_SYSTEM = "divert-system"
    ALLOW_ACTIVITY = "allow-activity"
    DENY_ACTIVITY = "deny-activity"
    ISOLATE_SYSTEM = "isolate-system"
    UPDATE_CONFIGURATION = "update-configuration"
    RESTORE_SYSTEM = "restore-system"
    PREPARE_SYSTEM = "prepare-system"
    MITIGATE_VULNERABILITY = "mitigate-vulnerability"
    ERADICATE_THREAT = "eradicate-threat"


class WorkflowStepType(str, Enum):
    START = "start"
    END = "end"
    ACTION = "action"
    PLAYBOOK_ACTION = "playbook-action"
    PARALLEL = "parallel"
    IF_CONDITION = "if-condition"
    WHILE_CONDITION = "while-condition"
    SWITCH_CONDITION = "switch-condition"


class CommandType(str, Enum):
    MANUAL = "manual"
    HTTP_API = "http-api"
    SSH = "ssh"
    BASH = "bash"
    CALDERA_CMD = "caldera-cmd"
    ELASTIC = "elastic"
    JUPYTER = "jupyter"
    KESTREL = "kestrel"
    OPENC2_HTTP = "openc2-http"
    OPENC2_MQTT = "openc2-mqtt"
    SIGMA = "sigma"
    YARA = "yara"


class AgentTargetType(str, Enum):
    GROUP = "group"
    INDIVIDUAL = "individual"
    LOCATION = "location"
    ORGANIZATION = "organization"
    SECTOR = "sector"
    SYSTEM = "system"
    HTTP_API = "http-api"
    SSH = "ssh"
    NET_ADDRESS = "net-address"
    SECURITY_INFRASTRUCTURE = "security-infrastructure"
    L2_MAC = "l2-mac"


# ============================================================================
# ID Generator
# ============================================================================

def generate_cacao_id(prefix: str) -> str:
    """Generate a CACAO-compliant identifier (prefix--uuid4)"""
    return f"{prefix}--{uuid.uuid4()}"


# ============================================================================
# Data Types (Section 10)
# ============================================================================

class Variable(BaseModel):
    """CACAO Variable (Section 10.18)"""
    type: str = Field(description="The type of variable: string, integer, long, boolean, float, dictionary, list, uuid, ipv4-addr, ipv6-addr, mac-addr, uri, sha256-hash, md5-hash, hex, iban, phone")
    description: Optional[str] = None
    value: Optional[str] = None
    constant: bool = Field(default=False, description="If true, the value cannot be changed at runtime")
    external: bool = Field(default=False, description="If true, the value is expected from an external source")


class Command(BaseModel):
    """CACAO Command Data Type (Section 5)"""
    type: CommandType = Field(description="The type of command")
    command: Optional[str] = Field(default=None, description="The actual command to execute")
    command_b64: Optional[str] = Field(default=None, description="Base64 encoded command")
    description: Optional[str] = None
    version: Optional[str] = None
    playbook_activity: Optional[PlaybookActivityType] = None
    headers: Optional[dict[str, str]] = None
    content: Optional[str] = None
    content_b64: Optional[str] = None

    @model_validator(mode="after")
    def validate_command_presence(self) -> "Command":
        if not self.command and not self.command_b64:
            raise ValueError("Either 'command' or 'command_b64' must be provided")
        return self


class AgentTarget(BaseModel):
    """CACAO Agent/Target (Section 7)"""
    type: AgentTargetType
    name: str
    description: Optional[str] = None
    location: Optional[dict[str, Any]] = None
    contact: Optional[dict[str, Any]] = None
    logical: Optional[list[str]] = None
    sector: Optional[str] = None
    address: Optional[dict[str, Any]] = None
    port: Optional[str] = None
    authentication_info: Optional[str] = None
    category: Optional[list[str]] = None


class AuthenticationInfo(BaseModel):
    """CACAO Authentication Information (Section 6)"""
    type: str = Field(description="e.g., http-basic, oauth2, user-auth, etc.")
    name: Optional[str] = None
    description: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    oauth_header: Optional[str] = None
    kms: bool = False
    kms_key_identifier: Optional[str] = None


# ============================================================================
# Workflow Steps (Section 4)
# ============================================================================

class WorkflowStep(BaseModel):
    """Base CACAO Workflow Step (Section 4)"""
    type: WorkflowStepType
    name: Optional[str] = None
    description: Optional[str] = None
    external_references: Optional[list[dict[str, str]]] = None
    delay: Optional[int] = Field(default=None, description="Delay in milliseconds before step executes")
    timeout: Optional[int] = Field(default=None, description="Timeout in milliseconds for step execution")
    step_variables: Optional[dict[str, Variable]] = None
    owner: Optional[str] = Field(default=None, description="ID of the agent responsible for this step")
    on_completion: Optional[str] = Field(default=None, description="ID of the next step to execute")
    on_success: Optional[str] = Field(default=None, description="ID of next step if successful")
    on_failure: Optional[str] = Field(default=None, description="ID of next step if failed")
    step_extensions: Optional[dict[str, Any]] = None

    # Action step specific
    commands: Optional[list[Command]] = None
    agent: Optional[str] = Field(default=None, description="ID of the agent executing this step")
    targets: Optional[list[str]] = Field(default=None, description="IDs of targets for this step")
    in_args: Optional[list[str]] = None
    out_args: Optional[list[str]] = None
    playbook_activity: Optional[PlaybookActivityType] = None

    # Playbook-action specific
    playbook_id: Optional[str] = None

    # If-condition specific
    condition: Optional[str] = Field(default=None, description="Boolean expression to evaluate")
    on_true: Optional[str] = None
    on_false: Optional[str] = None

    # While-condition specific (uses condition + on_true)

    # Switch-condition specific
    switch: Optional[str] = None
    cases: Optional[dict[str, str]] = Field(default=None, description="Map of case values to step IDs")

    # Parallel specific
    next_steps: Optional[list[str]] = Field(default=None, description="Steps to execute in parallel")

    @model_validator(mode="after")
    def validate_step_type(self) -> "WorkflowStep":
        if self.type == WorkflowStepType.ACTION and not self.commands:
            # Allow empty commands for manual steps
            pass
        if self.type == WorkflowStepType.IF_CONDITION and not self.condition:
            raise ValueError("If-condition step requires a 'condition'")
        if self.type == WorkflowStepType.WHILE_CONDITION and not self.condition:
            raise ValueError("While-condition step requires a 'condition'")
        if self.type == WorkflowStepType.PARALLEL and not self.next_steps:
            raise ValueError("Parallel step requires 'next_steps'")
        return self


# ============================================================================
# Playbook (Section 3) — Top-Level Object
# ============================================================================

class CacaoPlaybook(BaseModel):
    """
    CACAO v2.0 Playbook - Top Level Object
    This is the root object that represents a complete CACAO playbook.
    """
    type: str = Field(default="playbook", description="Must be 'playbook'")
    spec_version: str = Field(default="cacao-2.0", description="CACAO specification version")
    id: str = Field(default_factory=lambda: generate_cacao_id("playbook"), description="Unique playbook identifier")
    name: str = Field(description="Name of the playbook")
    description: Optional[str] = Field(default=None, description="Detailed description of the playbook")
    playbook_types: list[PlaybookType] = Field(default_factory=list, description="Operational roles addressed")
    playbook_activities: Optional[list[PlaybookActivityType]] = None

    created_by: str = Field(
        default_factory=lambda: generate_cacao_id("identity"),
        description="STIX 2.1 identity ID of creator"
    )
    created: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        description="Timestamp of initial creation"
    )
    modified: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        description="Timestamp of last modification"
    )

    revoked: bool = Field(default=False)
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    derived_from: Optional[list[str]] = None
    related_to: Optional[list[str]] = None

    priority: Optional[int] = Field(default=None, ge=0, le=100, description="Priority (1=highest, 100=lowest)")
    severity: Optional[int] = Field(default=None, ge=0, le=100, description="Severity (1=lowest, 100=highest)")
    impact: Optional[int] = Field(default=None, ge=0, le=100, description="Impact (1=lowest, 100=highest)")

    industry_sectors: Optional[list[str]] = None
    labels: Optional[list[str]] = None
    external_references: Optional[list[dict[str, str]]] = None
    features: Optional[dict[str, bool]] = None
    markings: Optional[list[str]] = None

    # Core workflow
    workflow_start: str = Field(description="ID of the first workflow step")
    workflow_exception: Optional[str] = Field(default=None, description="ID of the exception handler step")
    workflow: dict[str, WorkflowStep] = Field(description="Dictionary of workflow step objects")

    # Playbook variables
    playbook_variables: Optional[dict[str, Variable]] = None

    # Agents and Targets
    agent_definitions: Optional[dict[str, AgentTarget]] = None
    target_definitions: Optional[dict[str, AgentTarget]] = None

    # Authentication
    authentication_info_definitions: Optional[dict[str, AuthenticationInfo]] = None

    # Extensions
    extension_definitions: Optional[dict[str, Any]] = None
    data_marking_definitions: Optional[dict[str, Any]] = None
    signatures: Optional[list[dict[str, Any]]] = None

    @model_validator(mode="after")
    def validate_workflow(self) -> "CacaoPlaybook":
        """Validate workflow integrity"""
        if self.workflow_start not in self.workflow:
            raise ValueError(f"workflow_start '{self.workflow_start}' not found in workflow steps")

        # Validate start step exists and is correct type
        start_step = self.workflow[self.workflow_start]
        if start_step.type != WorkflowStepType.START:
            raise ValueError(f"workflow_start must point to a 'start' type step")

        # Validate all step references point to existing steps
        for step_id, step in self.workflow.items():
            refs = []
            if step.on_completion:
                refs.append(step.on_completion)
            if step.on_success:
                refs.append(step.on_success)
            if step.on_failure:
                refs.append(step.on_failure)
            if step.on_true:
                refs.append(step.on_true)
            if step.on_false:
                refs.append(step.on_false)
            if step.next_steps:
                refs.extend(step.next_steps)
            if step.cases:
                refs.extend(step.cases.values())

            for ref in refs:
                if ref not in self.workflow:
                    raise ValueError(
                        f"Step '{step_id}' references '{ref}' which does not exist in workflow"
                    )

        return self

    def to_json(self, indent: int = 2, exclude_none: bool = True) -> str:
        """Serialize playbook to CACAO JSON string"""
        import json
        data = self.model_dump(exclude_none=exclude_none)
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "CacaoPlaybook":
        """Deserialize playbook from JSON string"""
        import json
        data = json.loads(json_str)
        return cls(**data)

    def get_steps_in_order(self) -> list[tuple[str, WorkflowStep]]:
        """Walk the workflow and return steps in execution order (simple linear walk)"""
        visited = []
        current_id = self.workflow_start

        while current_id and current_id not in [v[0] for v in visited]:
            step = self.workflow.get(current_id)
            if not step:
                break
            visited.append((current_id, step))

            # Follow the primary path
            if step.on_completion:
                current_id = step.on_completion
            elif step.on_true:
                current_id = step.on_true
            elif step.next_steps:
                current_id = step.next_steps[0] if step.next_steps else None
            else:
                break

        return visited

    def get_action_steps(self) -> list[tuple[str, WorkflowStep]]:
        """Get only action steps (filtering start/end)"""
        return [
            (sid, step) for sid, step in self.get_steps_in_order()
            if step.type == WorkflowStepType.ACTION
        ]

    def add_step(
        self,
        step_type: WorkflowStepType,
        name: str,
        description: Optional[str] = None,
        commands: Optional[list[Command]] = None,
        **kwargs
    ) -> str:
        """Add a new step to the workflow and return its ID"""
        step_id = generate_cacao_id(step_type.value.replace("-", "-"))
        step = WorkflowStep(
            type=step_type,
            name=name,
            description=description,
            commands=commands,
            **kwargs
        )
        self.workflow[step_id] = step
        return step_id

    def summary(self) -> dict[str, Any]:
        """Return a summary of the playbook"""
        step_types = {}
        for step in self.workflow.values():
            t = step.type.value
            step_types[t] = step_types.get(t, 0) + 1

        return {
            "id": self.id,
            "name": self.name,
            "playbook_types": [pt.value for pt in self.playbook_types],
            "total_steps": len(self.workflow),
            "step_types": step_types,
            "action_steps": step_types.get("action", 0),
            "has_conditions": "if-condition" in step_types or "switch-condition" in step_types,
            "has_parallel": "parallel" in step_types,
            "has_variables": bool(self.playbook_variables),
            "has_agents": bool(self.agent_definitions),
            "has_targets": bool(self.target_definitions),
        }
