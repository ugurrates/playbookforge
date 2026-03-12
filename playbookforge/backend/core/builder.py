"""
PlaybookForge - CACAO v2.0 Playbook Builder
Fluent API for building CACAO playbooks programmatically.
"""

from __future__ import annotations

from typing import Any, Optional

from .cacao_model import (
    AgentTarget,
    AgentTargetType,
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


class PlaybookBuilder:
    """
    Fluent builder for creating CACAO v2.0 playbooks.
    
    Usage:
        pb = (
            PlaybookBuilder("Phishing Email Response")
            .set_description("Investigate and remediate phishing emails")
            .add_type(PlaybookType.INVESTIGATION)
            .add_type(PlaybookType.REMEDIATION)
            .add_label("phishing")
            .add_label("email-security")
            .add_mitre_reference("T1566.001", "Spearphishing Attachment")
            .add_action_step(
                name="Extract IOCs from email",
                description="Parse email headers and extract sender, URLs, attachments",
                commands=[Command(type=CommandType.HTTP_API, command="GET /api/email/parse")]
            )
            .add_if_condition(
                name="Check if IOCs are malicious",
                condition="$$malicious$$ == true",
                on_true_name="Block sender",
                on_false_name="Close case"
            )
            .add_action_step(
                name="Block sender",
                description="Add sender to blocklist",
                commands=[Command(type=CommandType.HTTP_API, command="POST /api/blocklist")]
            )
            .build()
        )
    """

    def __init__(self, name: str):
        self._name = name
        self._description: Optional[str] = None
        self._playbook_types: list[PlaybookType] = []
        self._playbook_activities: list[PlaybookActivityType] = []
        self._labels: list[str] = []
        self._external_references: list[dict[str, str]] = []
        self._variables: dict[str, Variable] = {}
        self._agent_definitions: dict[str, AgentTarget] = {}
        self._target_definitions: dict[str, AgentTarget] = {}
        self._priority: Optional[int] = None
        self._severity: Optional[int] = None
        self._impact: Optional[int] = None
        self._industry_sectors: list[str] = []
        self._created_by: Optional[str] = None

        # Internal step tracking
        self._steps: list[dict[str, Any]] = []
        self._pending_branches: dict[str, list] = {}

    # ── Metadata ─────────────────────────────────────────────────────────

    def set_description(self, description: str) -> "PlaybookBuilder":
        self._description = description
        return self

    def add_type(self, playbook_type: PlaybookType) -> "PlaybookBuilder":
        if playbook_type not in self._playbook_types:
            self._playbook_types.append(playbook_type)
        return self

    def add_activity(self, activity: PlaybookActivityType) -> "PlaybookBuilder":
        if activity not in self._playbook_activities:
            self._playbook_activities.append(activity)
        return self

    def add_label(self, label: str) -> "PlaybookBuilder":
        if label not in self._labels:
            self._labels.append(label)
        return self

    def set_priority(self, priority: int) -> "PlaybookBuilder":
        self._priority = priority
        return self

    def set_severity(self, severity: int) -> "PlaybookBuilder":
        self._severity = severity
        return self

    def set_impact(self, impact: int) -> "PlaybookBuilder":
        self._impact = impact
        return self

    def set_created_by(self, identity_id: str) -> "PlaybookBuilder":
        self._created_by = identity_id
        return self

    def add_industry_sector(self, sector: str) -> "PlaybookBuilder":
        if sector not in self._industry_sectors:
            self._industry_sectors.append(sector)
        return self

    def add_mitre_reference(self, technique_id: str, technique_name: str = "") -> "PlaybookBuilder":
        ref = {
            "name": f"MITRE ATT&CK - {technique_id}",
            "source": "MITRE ATT&CK",
            "url": f"https://attack.mitre.org/techniques/{technique_id.replace('.', '/')}/",
        }
        if technique_name:
            ref["description"] = technique_name
        self._external_references.append(ref)
        return self

    def add_external_reference(self, name: str, url: str, description: str = "") -> "PlaybookBuilder":
        ref = {"name": name, "url": url}
        if description:
            ref["description"] = description
        self._external_references.append(ref)
        return self

    # ── Variables ────────────────────────────────────────────────────────

    def add_variable(
        self,
        name: str,
        var_type: str = "string",
        value: Optional[str] = None,
        constant: bool = False,
        external: bool = False,
        description: Optional[str] = None,
    ) -> "PlaybookBuilder":
        self._variables[name] = Variable(
            type=var_type,
            value=value,
            constant=constant,
            external=external,
            description=description,
        )
        return self

    # ── Agents & Targets ─────────────────────────────────────────────────

    def add_agent(
        self,
        name: str,
        agent_type: AgentTargetType = AgentTargetType.ORGANIZATION,
        **kwargs,
    ) -> str:
        agent_id = generate_cacao_id("individual" if agent_type == AgentTargetType.INDIVIDUAL else "organization")
        self._agent_definitions[agent_id] = AgentTarget(
            type=agent_type, name=name, **kwargs
        )
        return agent_id

    def add_target(
        self,
        name: str,
        target_type: AgentTargetType = AgentTargetType.HTTP_API,
        **kwargs,
    ) -> str:
        target_id = generate_cacao_id(target_type.value)
        self._target_definitions[target_id] = AgentTarget(
            type=target_type, name=name, **kwargs
        )
        return target_id

    # ── Workflow Steps ───────────────────────────────────────────────────

    def add_action_step(
        self,
        name: str,
        description: Optional[str] = None,
        commands: Optional[list[Command]] = None,
        agent: Optional[str] = None,
        targets: Optional[list[str]] = None,
        activity: Optional[PlaybookActivityType] = None,
        on_failure_name: Optional[str] = None,
    ) -> "PlaybookBuilder":
        self._steps.append({
            "type": WorkflowStepType.ACTION,
            "name": name,
            "description": description,
            "commands": commands,
            "agent": agent,
            "targets": targets,
            "playbook_activity": activity,
            "_on_failure_name": on_failure_name,
        })
        return self

    def add_manual_step(
        self,
        name: str,
        description: str,
    ) -> "PlaybookBuilder":
        """Add a manual action step (no automated commands)"""
        self._steps.append({
            "type": WorkflowStepType.ACTION,
            "name": name,
            "description": description,
            "commands": [Command(type=CommandType.MANUAL, command=description)],
        })
        return self

    def add_if_condition(
        self,
        name: str,
        condition: str,
        on_true_name: Optional[str] = None,
        on_false_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PlaybookBuilder":
        self._steps.append({
            "type": WorkflowStepType.IF_CONDITION,
            "name": name,
            "condition": condition,
            "description": description,
            "_on_true_name": on_true_name,
            "_on_false_name": on_false_name,
        })
        return self

    def add_parallel_steps(
        self,
        name: str,
        parallel_step_names: list[str],
        description: Optional[str] = None,
    ) -> "PlaybookBuilder":
        self._steps.append({
            "type": WorkflowStepType.PARALLEL,
            "name": name,
            "description": description,
            "_parallel_names": parallel_step_names,
        })
        return self

    def add_playbook_action(
        self,
        name: str,
        playbook_id: str,
        description: Optional[str] = None,
    ) -> "PlaybookBuilder":
        self._steps.append({
            "type": WorkflowStepType.PLAYBOOK_ACTION,
            "name": name,
            "description": description,
            "playbook_id": playbook_id,
        })
        return self

    # ── Build ────────────────────────────────────────────────────────────

    def build(self) -> CacaoPlaybook:
        """Build the CACAO playbook from accumulated configuration"""
        workflow: dict[str, WorkflowStep] = {}

        # Create start step
        start_id = generate_cacao_id("start")
        end_id = generate_cacao_id("end")

        # Build step ID map (name → id) for cross-referencing
        step_ids: dict[int, str] = {}
        step_name_to_id: dict[str, str] = {}

        for i, step_def in enumerate(self._steps):
            st = step_def["type"]
            prefix = st.value
            sid = generate_cacao_id(prefix)
            step_ids[i] = sid
            if step_def.get("name"):
                step_name_to_id[step_def["name"]] = sid

        # Helper to resolve name → id
        def resolve_name(name: Optional[str]) -> Optional[str]:
            if not name:
                return None
            return step_name_to_id.get(name)

        # Build workflow steps
        for i, step_def in enumerate(self._steps):
            sid = step_ids[i]

            # Determine on_completion (next step in sequence or end)
            if i + 1 < len(self._steps):
                default_next = step_ids[i + 1]
            else:
                default_next = end_id

            step_kwargs: dict[str, Any] = {
                "type": step_def["type"],
                "name": step_def.get("name"),
                "description": step_def.get("description"),
            }

            if step_def["type"] == WorkflowStepType.ACTION:
                step_kwargs["commands"] = step_def.get("commands")
                step_kwargs["agent"] = step_def.get("agent")
                step_kwargs["targets"] = step_def.get("targets")
                step_kwargs["playbook_activity"] = step_def.get("playbook_activity")
                step_kwargs["on_completion"] = default_next
                if step_def.get("_on_failure_name"):
                    step_kwargs["on_failure"] = resolve_name(step_def["_on_failure_name"])

            elif step_def["type"] == WorkflowStepType.IF_CONDITION:
                step_kwargs["condition"] = step_def["condition"]
                step_kwargs["on_true"] = resolve_name(step_def.get("_on_true_name")) or default_next
                step_kwargs["on_false"] = resolve_name(step_def.get("_on_false_name")) or end_id

            elif step_def["type"] == WorkflowStepType.PARALLEL:
                parallel_names = step_def.get("_parallel_names", [])
                step_kwargs["next_steps"] = [
                    resolve_name(n) or default_next for n in parallel_names
                ]
                step_kwargs["on_completion"] = default_next

            elif step_def["type"] == WorkflowStepType.PLAYBOOK_ACTION:
                step_kwargs["playbook_id"] = step_def.get("playbook_id")
                step_kwargs["on_completion"] = default_next

            workflow[sid] = WorkflowStep(**step_kwargs)

        # Wire start step
        first_step_id = step_ids[0] if step_ids else end_id
        workflow[start_id] = WorkflowStep(
            type=WorkflowStepType.START,
            name="Start",
            on_completion=first_step_id,
        )

        # Wire end step
        workflow[end_id] = WorkflowStep(
            type=WorkflowStepType.END,
            name="End",
        )

        # Build playbook
        pb_kwargs: dict[str, Any] = {
            "name": self._name,
            "workflow_start": start_id,
            "workflow": workflow,
        }

        if self._description:
            pb_kwargs["description"] = self._description
        if self._playbook_types:
            pb_kwargs["playbook_types"] = self._playbook_types
        if self._playbook_activities:
            pb_kwargs["playbook_activities"] = self._playbook_activities
        if self._labels:
            pb_kwargs["labels"] = self._labels
        if self._external_references:
            pb_kwargs["external_references"] = self._external_references
        if self._variables:
            pb_kwargs["playbook_variables"] = self._variables
        if self._agent_definitions:
            pb_kwargs["agent_definitions"] = self._agent_definitions
        if self._target_definitions:
            pb_kwargs["target_definitions"] = self._target_definitions
        if self._priority is not None:
            pb_kwargs["priority"] = self._priority
        if self._severity is not None:
            pb_kwargs["severity"] = self._severity
        if self._impact is not None:
            pb_kwargs["impact"] = self._impact
        if self._industry_sectors:
            pb_kwargs["industry_sectors"] = self._industry_sectors
        if self._created_by:
            pb_kwargs["created_by"] = self._created_by

        return CacaoPlaybook(**pb_kwargs)
