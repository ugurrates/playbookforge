"""
PlaybookForge - Shuffle SOAR Exporter
Converts CACAO v2.0 playbooks to Shuffle workflow JSON format.

Shuffle Workflow Format:
- JSON-based, action-oriented
- Actions have: id, app_name, app_version, name, parameters
- Triggers start the workflow
- Branches connect actions via source_id/destination_id
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from ..core.cacao_model import (
    CacaoPlaybook,
    CommandType,
    WorkflowStep,
    WorkflowStepType,
)
from .base import BaseExporter


class ShuffleExporter(BaseExporter):
    """Export CACAO playbooks to Shuffle workflow JSON format"""

    @property
    def platform_name(self) -> str:
        return "Shuffle SOAR"

    @property
    def platform_id(self) -> str:
        return "shuffle"

    @property
    def file_extension(self) -> str:
        return ".json"

    def export(self, playbook: CacaoPlaybook) -> str:
        workflow = self._build_shuffle_workflow(playbook)
        return json.dumps(workflow, indent=2, ensure_ascii=False)

    def export_to_dict(self, playbook: CacaoPlaybook) -> dict[str, Any]:
        return self._build_shuffle_workflow(playbook)

    def _build_shuffle_workflow(self, playbook: CacaoPlaybook) -> dict[str, Any]:
        """Build the Shuffle workflow structure"""

        # Map CACAO step IDs to Shuffle action UUIDs
        step_id_map: dict[str, str] = {}
        for step_id in playbook.workflow:
            step_id_map[step_id] = str(uuid.uuid4())

        # Build actions
        actions = []
        triggers = []
        branches = []

        x_pos, y_pos = 100, 100

        for step_id, step in playbook.workflow.items():
            shuffle_id = step_id_map[step_id]

            if step.type == WorkflowStepType.START:
                # Create a trigger for the start step
                trigger = self._create_trigger(step, shuffle_id, x_pos, y_pos)
                triggers.append(trigger)

                # Connect trigger to first action
                if step.on_completion and step.on_completion in step_id_map:
                    branches.append(self._create_branch(
                        shuffle_id,
                        step_id_map[step.on_completion],
                        label="",
                    ))

            elif step.type == WorkflowStepType.END:
                # End step becomes a final action
                actions.append({
                    "id": shuffle_id,
                    "app_name": "Shuffle Tools",
                    "app_version": "1.2.0",
                    "app_id": "",
                    "name": step.name or "End",
                    "label": step.name or "Workflow Complete",
                    "environment": "Shuffle",
                    "is_start_node": False,
                    "position": {"x": x_pos, "y": y_pos},
                    "parameters": [],
                    "errors": [],
                    "large_image": "",
                })

            elif step.type == WorkflowStepType.ACTION:
                action = self._create_action(step, shuffle_id, x_pos, y_pos)
                actions.append(action)

                # Create branches for connections
                if step.on_completion and step.on_completion in step_id_map:
                    branches.append(self._create_branch(
                        shuffle_id,
                        step_id_map[step.on_completion],
                    ))
                if step.on_success and step.on_success in step_id_map:
                    branches.append(self._create_branch(
                        shuffle_id,
                        step_id_map[step.on_success],
                        label="success",
                    ))
                if step.on_failure and step.on_failure in step_id_map:
                    branches.append(self._create_branch(
                        shuffle_id,
                        step_id_map[step.on_failure],
                        label="failure",
                        has_errors=True,
                    ))

            elif step.type == WorkflowStepType.IF_CONDITION:
                # Conditions become actions with branching
                condition_action = self._create_condition_action(step, shuffle_id, x_pos, y_pos)
                actions.append(condition_action)

                if step.on_true and step.on_true in step_id_map:
                    branches.append(self._create_branch(
                        shuffle_id,
                        step_id_map[step.on_true],
                        label="true",
                        condition=step.condition or "",
                    ))
                if step.on_false and step.on_false in step_id_map:
                    branches.append(self._create_branch(
                        shuffle_id,
                        step_id_map[step.on_false],
                        label="false",
                    ))

            elif step.type == WorkflowStepType.PARALLEL:
                # Parallel becomes multiple branches from one action
                parallel_action = {
                    "id": shuffle_id,
                    "app_name": "Shuffle Tools",
                    "app_version": "1.2.0",
                    "app_id": "",
                    "name": "run_parallel",
                    "label": step.name or "Parallel Execution",
                    "environment": "Shuffle",
                    "is_start_node": False,
                    "position": {"x": x_pos, "y": y_pos},
                    "parameters": [],
                    "errors": [],
                }
                actions.append(parallel_action)

                if step.next_steps:
                    for ns in step.next_steps:
                        if ns in step_id_map:
                            branches.append(self._create_branch(shuffle_id, step_id_map[ns]))

            y_pos += 150

        # Build complete workflow
        workflow = {
            "name": playbook.name,
            "description": playbook.description or "",
            "id": str(uuid.uuid4()),
            "start": step_id_map.get(playbook.workflow_start, ""),
            "org_id": "",
            "status": "test",
            "is_valid": True,
            "actions": actions,
            "triggers": triggers,
            "branches": branches,
            "workflow_variables": self._convert_variables(playbook),
            "tags": playbook.labels or [],
            "default_return_value": "",
            "execution_environment": "Shuffle",
            "previously_saved": False,
            "_playbookforge_metadata": {
                "source_format": "cacao-2.0",
                "source_id": playbook.id,
                "converter": "PlaybookForge",
            },
        }

        return workflow

    def _create_trigger(self, step: WorkflowStep, trigger_id: str, x: int, y: int) -> dict[str, Any]:
        """Create a Shuffle trigger from a CACAO start step"""
        return {
            "id": trigger_id,
            "name": step.name or "Start Trigger",
            "description": step.description or "Workflow trigger",
            "trigger_type": "WEBHOOK",
            "status": "running",
            "label": step.name or "Webhook",
            "position": {"x": x, "y": y},
            "parameters": [],
            "environment": "Shuffle",
            "is_valid": True,
        }

    def _create_action(self, step: WorkflowStep, action_id: str, x: int, y: int) -> dict[str, Any]:
        """Create a Shuffle action from a CACAO action step"""
        app_name, app_action = self._resolve_app(step)
        parameters = self._build_parameters(step)

        return {
            "id": action_id,
            "app_name": app_name,
            "app_version": "1.0.0",
            "app_id": "",
            "name": app_action,
            "label": step.name or f"Action",
            "description": step.description or "",
            "environment": "Shuffle",
            "is_start_node": False,
            "position": {"x": x, "y": y},
            "parameters": parameters,
            "errors": [],
            "large_image": "",
        }

    def _create_condition_action(self, step: WorkflowStep, action_id: str, x: int, y: int) -> dict[str, Any]:
        """Create a Shuffle condition action"""
        return {
            "id": action_id,
            "app_name": "Shuffle Tools",
            "app_version": "1.2.0",
            "app_id": "",
            "name": "filter_list",
            "label": step.name or "Condition",
            "description": step.description or f"Condition: {step.condition}",
            "environment": "Shuffle",
            "is_start_node": False,
            "position": {"x": x, "y": y},
            "parameters": [
                {
                    "name": "input_list",
                    "value": step.condition or "",
                    "description": "Condition expression from CACAO",
                }
            ],
            "errors": [],
        }

    def _create_branch(
        self,
        source_id: str,
        dest_id: str,
        label: str = "",
        condition: str = "",
        has_errors: bool = False,
    ) -> dict[str, Any]:
        """Create a Shuffle branch (connection between actions)"""
        branch: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "source_id": source_id,
            "destination_id": dest_id,
            "label": label,
            "has_errors": has_errors,
        }
        if condition:
            branch["conditions"] = [
                {
                    "condition": {"value": condition},
                    "source": {"id": source_id},
                    "destination": {"id": dest_id},
                }
            ]
        return branch

    def _resolve_app(self, step: WorkflowStep) -> tuple[str, str]:
        """Map CACAO commands to Shuffle app name and action"""
        if not step.commands:
            return "Shuffle Tools", "execute_bash"

        cmd = step.commands[0]

        app_mapping: dict[CommandType, tuple[str, str]] = {
            CommandType.HTTP_API: ("HTTP", "curl"),
            CommandType.BASH: ("Shuffle Tools", "execute_bash"),
            CommandType.SSH: ("SSH", "exec_command"),
            CommandType.MANUAL: ("Shuffle Tools", "send_email_shuffle"),
            CommandType.SIGMA: ("Shuffle Tools", "execute_bash"),
            CommandType.YARA: ("Shuffle Tools", "execute_bash"),
        }

        return app_mapping.get(cmd.type, ("Shuffle Tools", "execute_bash"))

    def _build_parameters(self, step: WorkflowStep) -> list[dict[str, str]]:
        """Build Shuffle action parameters from CACAO step"""
        params = []

        if step.commands:
            cmd = step.commands[0]
            if cmd.type == CommandType.HTTP_API and cmd.command:
                parts = cmd.command.strip().split(maxsplit=1)
                if len(parts) >= 2:
                    params.append({"name": "method", "value": parts[0]})
                    params.append({"name": "url", "value": parts[1]})
                elif len(parts) == 1:
                    params.append({"name": "url", "value": parts[0]})
                if cmd.headers:
                    import json
                    params.append({"name": "headers", "value": json.dumps(cmd.headers)})
                if cmd.content:
                    params.append({"name": "body", "value": cmd.content})

            elif cmd.type in (CommandType.BASH, CommandType.SSH):
                params.append({"name": "command", "value": cmd.command or ""})

            elif cmd.type == CommandType.MANUAL:
                params.append({"name": "body", "value": cmd.command or step.description or ""})

        return params

    def _convert_variables(self, playbook: CacaoPlaybook) -> list[dict[str, str]]:
        """Convert CACAO variables to Shuffle workflow variables"""
        variables = []
        if playbook.playbook_variables:
            for name, var in playbook.playbook_variables.items():
                variables.append({
                    "name": name,
                    "value": var.value or "",
                    "description": var.description or "",
                    "id": str(uuid.uuid4()),
                })
        return variables
