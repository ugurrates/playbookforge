"""
PlaybookForge - Cortex XSOAR Exporter
Converts CACAO v2.0 playbooks to Palo Alto Cortex XSOAR YAML format.

XSOAR Playbook Format:
- YAML-based, task-oriented
- Tasks have: id, taskid, type, task (name, iscommand, script, etc.)
- Conditions map to conditional tasks
- Connections via nexttasks dict
"""

from __future__ import annotations

import uuid
from typing import Any

import yaml

from ..core.cacao_model import (
    CacaoPlaybook,
    CommandType,
    WorkflowStep,
    WorkflowStepType,
)
from .base import BaseExporter


class XSOARExporter(BaseExporter):
    """Export CACAO playbooks to Cortex XSOAR YAML format"""

    @property
    def platform_name(self) -> str:
        return "Palo Alto Cortex XSOAR"

    @property
    def platform_id(self) -> str:
        return "xsoar"

    @property
    def file_extension(self) -> str:
        return ".yml"

    def export(self, playbook: CacaoPlaybook) -> str:
        xsoar_pb = self._build_xsoar_playbook(playbook)
        return yaml.dump(xsoar_pb, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def export_to_dict(self, playbook: CacaoPlaybook) -> dict[str, Any]:
        return self._build_xsoar_playbook(playbook)

    def _build_xsoar_playbook(self, playbook: CacaoPlaybook) -> dict[str, Any]:
        """Build the XSOAR playbook structure"""

        # Map CACAO step IDs to XSOAR numeric task IDs
        step_id_map: dict[str, str] = {}
        task_counter = 0
        for step_id in playbook.workflow:
            step_id_map[step_id] = str(task_counter)
            task_counter += 1

        # Build tasks
        tasks: dict[str, dict] = {}
        for step_id, step in playbook.workflow.items():
            xsoar_task_id = step_id_map[step_id]
            task = self._convert_step_to_task(step, step_id, step_id_map, xsoar_task_id)
            tasks[xsoar_task_id] = task

        # Build XSOAR playbook structure
        xsoar_playbook = {
            "id": playbook.id.replace("playbook--", ""),
            "version": -1,
            "name": playbook.name,
            "description": playbook.description or "",
            "starttaskid": step_id_map.get(playbook.workflow_start, "0"),
            "tasks": tasks,
            "view": self._generate_view(tasks),
            "inputs": self._extract_inputs(playbook),
            "outputs": self._extract_outputs(playbook),
            "fromversion": "6.0.0",
            "tests": ["No tests"],
            "tags": playbook.labels or [],
        }

        return xsoar_playbook

    def _convert_step_to_task(
        self,
        step: WorkflowStep,
        step_id: str,
        step_id_map: dict[str, str],
        task_id: str,
    ) -> dict[str, Any]:
        """Convert a CACAO workflow step to an XSOAR task"""

        task_uuid = str(uuid.uuid4())

        # Determine XSOAR task type
        xsoar_type = self._map_step_type(step.type)

        # Build nexttasks (connections)
        nexttasks: dict[str, list[str]] = {}
        if step.on_completion and step.on_completion in step_id_map:
            nexttasks["#none#"] = [step_id_map[step.on_completion]]
        if step.on_success and step.on_success in step_id_map:
            nexttasks["#none#"] = [step_id_map[step.on_success]]
        if step.on_true and step.on_true in step_id_map:
            nexttasks["yes"] = [step_id_map[step.on_true]]
        if step.on_false and step.on_false in step_id_map:
            nexttasks["no"] = [step_id_map[step.on_false]]

        # Build task object
        task: dict[str, Any] = {
            "id": task_id,
            "taskid": task_uuid,
            "type": xsoar_type,
            "task": {
                "id": task_uuid,
                "version": -1,
                "name": step.name or f"Step {task_id}",
                "description": step.description or "",
                "type": xsoar_type,
                "iscommand": False,
            },
            "nexttasks": nexttasks,
            "separatecontext": False,
            "view": self._task_position(int(task_id)),
        }

        # Handle commands → XSOAR script/command
        if step.commands and step.type == WorkflowStepType.ACTION:
            cmd = step.commands[0]  # Primary command
            if cmd.type == CommandType.MANUAL:
                task["task"]["iscommand"] = False
                task["type"] = "regular"
                task["task"]["type"] = "regular"
            elif cmd.type == CommandType.HTTP_API:
                task["task"]["iscommand"] = True
                task["task"]["script"] = self._map_command_to_script(cmd)
                task["scriptarguments"] = self._extract_script_args(cmd)
            elif cmd.type in (CommandType.BASH, CommandType.SSH):
                task["task"]["iscommand"] = True
                task["task"]["script"] = "|||executeCommand"
                task["scriptarguments"] = {"command": {"simple": cmd.command or ""}}
            else:
                task["task"]["iscommand"] = True
                task["task"]["script"] = f"|||{cmd.type.value}"

        # Handle conditions
        if step.type == WorkflowStepType.IF_CONDITION:
            task["conditions"] = [
                {
                    "label": "yes",
                    "condition": [
                        [
                            {
                                "operator": "isNotEmpty",
                                "left": {"value": {"simple": step.condition or ""}},
                            }
                        ]
                    ],
                }
            ]

        return task

    def _map_step_type(self, step_type: WorkflowStepType) -> str:
        """Map CACAO step type to XSOAR task type"""
        mapping = {
            WorkflowStepType.START: "start",
            WorkflowStepType.END: "title",
            WorkflowStepType.ACTION: "regular",
            WorkflowStepType.PLAYBOOK_ACTION: "playbook",
            WorkflowStepType.IF_CONDITION: "condition",
            WorkflowStepType.WHILE_CONDITION: "condition",
            WorkflowStepType.SWITCH_CONDITION: "condition",
            WorkflowStepType.PARALLEL: "title",
        }
        return mapping.get(step_type, "regular")

    def _map_command_to_script(self, cmd: Any) -> str:
        """Map a CACAO command to an XSOAR script reference"""
        if cmd.command:
            # Attempt to extract meaningful command name
            parts = cmd.command.strip().split()
            if len(parts) >= 2:
                method = parts[0].upper()
                path = parts[1]
                # Convert API path to a reasonable script name
                path_parts = [p for p in path.split("/") if p and not p.startswith("{")]
                if path_parts:
                    return f"|||{'_'.join(path_parts[-2:])}"
            return f"|||custom_command"
        return "|||manual_task"

    def _extract_script_args(self, cmd: Any) -> dict[str, Any]:
        """Extract script arguments from a command"""
        args = {}
        if cmd.content:
            args["body"] = {"simple": cmd.content}
        if cmd.headers:
            for k, v in cmd.headers.items():
                args[k.lower().replace("-", "_")] = {"simple": v}
        return args

    def _extract_inputs(self, playbook: CacaoPlaybook) -> list[dict[str, Any]]:
        """Convert CACAO variables to XSOAR inputs"""
        inputs = []
        if playbook.playbook_variables:
            for name, var in playbook.playbook_variables.items():
                if var.external:
                    inputs.append({
                        "key": name,
                        "value": {"simple": var.value or ""},
                        "required": not var.value,
                        "description": var.description or "",
                        "playbookInputQuery": None,
                    })
        return inputs

    def _extract_outputs(self, playbook: CacaoPlaybook) -> list[dict[str, Any]]:
        """Convert CACAO output variables to XSOAR outputs"""
        outputs = []
        if playbook.playbook_variables:
            for name, var in playbook.playbook_variables.items():
                if not var.external and not var.constant:
                    outputs.append({
                        "contextPath": name,
                        "description": var.description or "",
                        "type": self._map_var_type(var.type),
                    })
        return outputs

    def _map_var_type(self, cacao_type: str) -> str:
        """Map CACAO variable type to XSOAR type"""
        type_map = {
            "string": "string",
            "integer": "number",
            "long": "number",
            "boolean": "boolean",
            "float": "number",
            "dictionary": "unknown",
            "list": "unknown",
            "ipv4-addr": "string",
            "ipv6-addr": "string",
            "uri": "string",
        }
        return type_map.get(cacao_type, "string")

    def _generate_view(self, tasks: dict) -> str:
        """Generate XSOAR canvas view JSON"""
        import json
        view = {
            "linkLabelsPosition": {},
            "paper": {"dimensions": {"height": max(len(tasks) * 200, 500), "width": 800}},
        }
        return json.dumps(view)

    def _task_position(self, index: int) -> str:
        """Generate task position on canvas"""
        import json
        return json.dumps({
            "position": {"x": 400, "y": 50 + (index * 200)},
        })
