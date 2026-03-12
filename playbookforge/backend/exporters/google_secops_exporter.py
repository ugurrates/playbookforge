"""
PlaybookForge - Google SecOps SOAR (Siemplify) Exporter
Converts CACAO v2.0 playbooks to Google SecOps SOAR format.

Google SecOps SOAR uses the Siemplify SDK pattern with Python-based actions.
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from ..core.cacao_model import (
    CacaoPlaybook,
    CommandType,
    WorkflowStep,
    WorkflowStepType,
)
from .base import BaseExporter


class GoogleSecOpsExporter(BaseExporter):
    """Export CACAO playbooks to Google SecOps SOAR format"""

    @property
    def platform_name(self) -> str:
        return "Google SecOps SOAR"

    @property
    def platform_id(self) -> str:
        return "google_secops"

    @property
    def file_extension(self) -> str:
        return ".json"

    def export(self, playbook: CacaoPlaybook) -> str:
        result = self._build_secops_playbook(playbook)
        return json.dumps(result, indent=2, ensure_ascii=False)

    def _build_secops_playbook(self, playbook: CacaoPlaybook) -> dict[str, Any]:
        """Build Google SecOps SOAR playbook structure."""
        ordered = playbook.get_steps_in_order()

        # Build actions
        actions: list[dict[str, Any]] = []
        flows: list[dict[str, Any]] = []
        action_uuid_map: dict[str, str] = {}

        for step_id, step in ordered:
            if step.type in (WorkflowStepType.START, WorkflowStepType.END):
                continue

            action_id = str(uuid.uuid4())
            action_uuid_map[step_id] = action_id

            if step.type == WorkflowStepType.IF_CONDITION:
                actions.append(self._build_condition_action(step, action_id))
            elif step.type == WorkflowStepType.PARALLEL:
                actions.append(self._build_parallel_action(step, action_id))
            else:
                actions.append(self._build_action(step, action_id))

        # Build flows (connections between actions)
        prev_action_id = None
        for step_id, step in ordered:
            if step.type in (WorkflowStepType.START, WorkflowStepType.END):
                continue

            action_id = action_uuid_map.get(step_id)
            if prev_action_id and action_id:
                flows.append({
                    "id": str(uuid.uuid4()),
                    "source_action_id": prev_action_id,
                    "target_action_id": action_id,
                    "type": "default",
                })
            prev_action_id = action_id

        # Build the playbook definition
        playbook_def = {
            "name": playbook.name,
            "description": playbook.description or "",
            "id": str(uuid.uuid4()),
            "version": "1.0",
            "priority": playbook.priority or 0,
            "is_enabled": True,
            "trigger": {
                "type": "ALERT",
                "description": "Triggered on alert creation",
                "id": str(uuid.uuid4()),
            },
            "actions": actions,
            "flows": flows,
            "tags": playbook.labels or [],
            "category": "investigation",
            "environment": "Default Environment",
            "_playbookforge_metadata": {
                "source_format": "cacao-2.0",
                "source_id": playbook.id,
                "converter": "PlaybookForge",
            },
        }

        # Build individual action scripts
        action_scripts: list[dict[str, Any]] = []
        for step_id, step in ordered:
            if step.type in (WorkflowStepType.START, WorkflowStepType.END, WorkflowStepType.IF_CONDITION):
                continue
            script = self._generate_action_script(step)
            action_scripts.append({
                "name": self._safe_name(step.name or "action"),
                "script": script,
                "integration": self._resolve_integration(step),
            })

        return {
            "playbook": playbook_def,
            "action_scripts": action_scripts,
        }

    def _build_action(self, step: WorkflowStep, action_id: str) -> dict[str, Any]:
        """Build a Google SecOps action."""
        integration, action_name = self._resolve_integration_and_action(step)

        params: list[dict[str, str]] = []
        if step.commands:
            cmd = step.commands[0]
            if cmd.command:
                params.append({"name": "command", "value": cmd.command})
            if cmd.content:
                params.append({"name": "body", "value": cmd.content})

        return {
            "id": action_id,
            "name": step.name or "Action",
            "description": step.description or "",
            "type": "action",
            "integration": integration,
            "action_name": action_name,
            "parameters": params,
            "is_enabled": True,
            "entity_scope": "ALL",
        }

    def _build_condition_action(self, step: WorkflowStep, action_id: str) -> dict[str, Any]:
        """Build a condition/flow action."""
        return {
            "id": action_id,
            "name": step.name or "Condition",
            "description": step.description or "",
            "type": "condition",
            "condition": step.condition or "true",
            "true_branch": [],
            "false_branch": [],
            "is_enabled": True,
        }

    def _build_parallel_action(self, step: WorkflowStep, action_id: str) -> dict[str, Any]:
        """Build a parallel execution block."""
        return {
            "id": action_id,
            "name": step.name or "Parallel",
            "description": step.description or "",
            "type": "parallel",
            "parallel_actions": [],
            "is_enabled": True,
        }

    def _resolve_integration_and_action(self, step: WorkflowStep) -> tuple[str, str]:
        """Map CACAO commands to Google SecOps integration + action."""
        if not step.commands:
            return "Siemplify", "manual_action"

        cmd = step.commands[0]
        if cmd.type == CommandType.HTTP_API:
            return "HTTP", "send_request"
        if cmd.type == CommandType.BASH:
            return "Utilities", "execute_command"
        if cmd.type == CommandType.SSH:
            return "SSH", "execute_command"
        if cmd.type == CommandType.MANUAL:
            return "Siemplify", "manual_action"
        return "Siemplify", "custom_action"

    def _resolve_integration(self, step: WorkflowStep) -> str:
        integration, _ = self._resolve_integration_and_action(step)
        return integration

    def _generate_action_script(self, step: WorkflowStep) -> str:
        """Generate a Siemplify action Python script for a step."""
        func_name = self._safe_name(step.name or "action")
        integration, action_name = self._resolve_integration_and_action(step)

        script_lines = [
            "from SiemplifyAction import SiemplifyAction",
            "from SiemplifyUtils import output_handler",
            "from ScriptResult import EXECUTION_STATE_COMPLETED, EXECUTION_STATE_FAILED",
            "",
            f'INTEGRATION_NAME = "{integration}"',
            f'SCRIPT_NAME = "{func_name}"',
            "",
            "",
            "@output_handler",
            "def main():",
            "    siemplify = SiemplifyAction()",
            f'    siemplify.script_name = SCRIPT_NAME',
            f'    siemplify.LOGGER.info("--- Started ---")',
            "",
        ]

        if step.commands:
            cmd = step.commands[0]
            if cmd.type == CommandType.HTTP_API and cmd.command:
                parts = cmd.command.strip().split(maxsplit=1)
                method = parts[0] if parts else "GET"
                url = parts[1] if len(parts) > 1 else "/"
                script_lines.append(f'    method = "{method}"')
                script_lines.append(f'    url = "{url}"')
                if cmd.content:
                    script_lines.append(f"    body = '''{cmd.content}'''")
                script_lines.append("")
                script_lines.append("    # Execute HTTP request")
                script_lines.append('    siemplify.LOGGER.info(f"Executing {method} {url}")')
            elif cmd.type == CommandType.MANUAL:
                script_lines.append(f"    # Manual step: {cmd.command}")
        else:
            script_lines.append(f"    # {step.description or 'Execute action'}")

        script_lines.extend([
            "",
            "    result_value = True",
            "    status = EXECUTION_STATE_COMPLETED",
            f'    output_message = "{step.name or "Action"} completed successfully"',
            "",
            "    siemplify.result.add_result_json({})",
            "    siemplify.end(output_message, result_value, status)",
            "",
            "",
            'if __name__ == "__main__":',
            "    main()",
            "",
        ])

        return "\n".join(script_lines)

    def _safe_name(self, name: str) -> str:
        """Convert name to safe identifier."""
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", name.lower().strip())
        safe = re.sub(r"_+", "_", safe).strip("_")
        return safe or "action"
