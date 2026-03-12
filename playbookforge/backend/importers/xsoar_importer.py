"""
PlaybookForge - Cortex XSOAR Importer
Converts Cortex XSOAR YAML playbooks to CACAO v2.0 format.
"""

from __future__ import annotations

import yaml
from typing import Any, Optional

from ..core.cacao_model import (
    CacaoPlaybook,
    Command,
    CommandType,
    PlaybookType,
    Variable,
    WorkflowStep,
    WorkflowStepType,
    generate_cacao_id,
)
from .base import BaseImporter


class XSOARImporter(BaseImporter):
    """Import Cortex XSOAR YAML playbooks to CACAO v2.0"""

    @property
    def platform_name(self) -> str:
        return "Palo Alto Cortex XSOAR"

    @property
    def platform_id(self) -> str:
        return "xsoar"

    @property
    def supported_extensions(self) -> list[str]:
        return [".yml", ".yaml"]

    def detect(self, content: str) -> bool:
        """Detect XSOAR playbook format by looking for key markers."""
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return False
            return (
                "tasks" in data
                and "starttaskid" in data
                and isinstance(data.get("tasks"), dict)
            )
        except Exception:
            return False

    def parse(self, content: str) -> CacaoPlaybook:
        """Parse XSOAR YAML into a CACAO playbook."""
        data = yaml.safe_load(content)

        # Map XSOAR numeric task IDs to CACAO step IDs
        task_id_to_cacao_id: dict[str, str] = {}
        tasks: dict[str, dict] = data.get("tasks", {})

        for tid, task in tasks.items():
            xsoar_type = task.get("type", "regular")
            cacao_type = self._map_task_type(xsoar_type)
            prefix = cacao_type.value
            task_id_to_cacao_id[str(tid)] = generate_cacao_id(prefix)

        # Build workflow steps
        workflow: dict[str, WorkflowStep] = {}

        for tid, task in tasks.items():
            cacao_id = task_id_to_cacao_id[str(tid)]
            step = self._convert_task_to_step(task, task_id_to_cacao_id)
            workflow[cacao_id] = step

        # Determine start step
        start_task_id = str(data.get("starttaskid", "0"))
        workflow_start = task_id_to_cacao_id.get(start_task_id)

        if not workflow_start or workflow_start not in workflow:
            # Fallback: create a start step
            start_id = generate_cacao_id("start")
            first_step = list(workflow.keys())[0] if workflow else None
            workflow[start_id] = WorkflowStep(
                type=WorkflowStepType.START,
                name="Start",
                on_completion=first_step,
            )
            workflow_start = start_id

        # Ensure there's an end step
        has_end = any(s.type == WorkflowStepType.END for s in workflow.values())
        if not has_end:
            end_id = generate_cacao_id("end")
            workflow[end_id] = WorkflowStep(type=WorkflowStepType.END, name="End")
            # Wire dangling steps to end
            for step in workflow.values():
                if step.type not in (WorkflowStepType.END, WorkflowStepType.IF_CONDITION):
                    if not step.on_completion and not step.on_success:
                        step.on_completion = end_id

        # Build variables
        playbook_variables = self._extract_variables(data)

        # Build playbook
        pb = CacaoPlaybook(
            name=data.get("name", "Imported XSOAR Playbook"),
            description=data.get("description", ""),
            playbook_types=[PlaybookType.INVESTIGATION],
            workflow_start=workflow_start,
            workflow=workflow,
            playbook_variables=playbook_variables if playbook_variables else None,
            labels=data.get("tags") or None,
        )

        return pb

    def _map_task_type(self, xsoar_type: str) -> WorkflowStepType:
        """Map XSOAR task type to CACAO step type."""
        mapping = {
            "start": WorkflowStepType.START,
            "regular": WorkflowStepType.ACTION,
            "condition": WorkflowStepType.IF_CONDITION,
            "playbook": WorkflowStepType.PLAYBOOK_ACTION,
            "title": WorkflowStepType.ACTION,
        }
        return mapping.get(xsoar_type, WorkflowStepType.ACTION)

    def _convert_task_to_step(
        self,
        task: dict[str, Any],
        id_map: dict[str, str],
    ) -> WorkflowStep:
        """Convert an XSOAR task dict to a CACAO WorkflowStep."""
        xsoar_type = task.get("type", "regular")
        cacao_type = self._map_task_type(xsoar_type)
        task_info = task.get("task", {})

        kwargs: dict[str, Any] = {
            "type": cacao_type,
            "name": task_info.get("name") or task.get("id", ""),
            "description": task_info.get("description", ""),
        }

        # Map nexttasks
        nexttasks = task.get("nexttasks", {})
        if cacao_type == WorkflowStepType.IF_CONDITION:
            # Condition branching
            yes_targets = nexttasks.get("yes", [])
            no_targets = nexttasks.get("no", [])
            if yes_targets:
                kwargs["on_true"] = id_map.get(str(yes_targets[0]))
            if no_targets:
                kwargs["on_false"] = id_map.get(str(no_targets[0]))
            # Build condition from XSOAR conditions block
            conditions = task.get("conditions", [])
            if conditions:
                kwargs["condition"] = self._extract_condition(conditions)
            else:
                kwargs["condition"] = "true"
        else:
            # Linear flow
            default_targets = nexttasks.get("#none#", [])
            if default_targets:
                kwargs["on_completion"] = id_map.get(str(default_targets[0]))

        # Map commands
        if task_info.get("iscommand") and cacao_type == WorkflowStepType.ACTION:
            script = task_info.get("script", "")
            cmd_str = script.replace("|||", "").strip() if script else "manual"
            script_args = task.get("scriptarguments", {})
            content = None
            if script_args:
                import json
                content = json.dumps({k: v.get("simple", "") for k, v in script_args.items()})
            kwargs["commands"] = [
                Command(
                    type=CommandType.HTTP_API,
                    command=f"POST /api/{cmd_str}",
                    content=content,
                    description=task_info.get("description", ""),
                )
            ]
        elif cacao_type == WorkflowStepType.ACTION and xsoar_type != "start":
            kwargs["commands"] = [
                Command(
                    type=CommandType.MANUAL,
                    command=task_info.get("description") or task_info.get("name") or "Manual step",
                )
            ]

        # Playbook action
        if cacao_type == WorkflowStepType.PLAYBOOK_ACTION:
            kwargs["playbook_id"] = generate_cacao_id("playbook")
            # Ensure on_completion for playbook actions
            default_targets = nexttasks.get("#none#", [])
            if default_targets:
                kwargs["on_completion"] = id_map.get(str(default_targets[0]))

        return WorkflowStep(**kwargs)

    def _extract_condition(self, conditions: list[dict]) -> str:
        """Extract condition expression from XSOAR conditions block."""
        try:
            cond = conditions[0]
            inner = cond.get("condition", [[]])[0]
            if inner:
                left_val = inner[0].get("left", {}).get("value", {}).get("simple", "")
                operator = inner[0].get("operator", "isNotEmpty")
                return f"{left_val} {operator}"
        except (IndexError, KeyError, TypeError):
            pass
        return "true"

    def _extract_variables(self, data: dict) -> dict[str, Variable]:
        """Extract variables from XSOAR inputs/outputs."""
        variables: dict[str, Variable] = {}

        for inp in data.get("inputs", []):
            key = inp.get("key", "")
            if key:
                variables[key] = Variable(
                    type="string",
                    value=inp.get("value", {}).get("simple", ""),
                    external=True,
                    description=inp.get("description", ""),
                )

        for out in data.get("outputs", []):
            path = out.get("contextPath", "")
            if path:
                variables[path] = Variable(
                    type=out.get("type", "string"),
                    description=out.get("description", ""),
                )

        return variables
