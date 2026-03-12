"""
PlaybookForge - Microsoft Sentinel Importer
Converts Azure ARM Template (Logic Apps) JSON to CACAO v2.0 format.
"""

from __future__ import annotations

import json
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


class SentinelImporter(BaseImporter):
    """Import Microsoft Sentinel ARM Template (Logic Apps) to CACAO v2.0"""

    @property
    def platform_name(self) -> str:
        return "Microsoft Sentinel"

    @property
    def platform_id(self) -> str:
        return "sentinel"

    @property
    def supported_extensions(self) -> list[str]:
        return [".json"]

    def detect(self, content: str) -> bool:
        """Detect Sentinel ARM template format."""
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                return False
            schema = data.get("$schema", "")
            resources = data.get("resources", [])
            is_arm = "schema.management.azure.com" in schema
            has_logic_app = any(
                r.get("type") == "Microsoft.Logic/workflows"
                for r in resources
            ) if resources else False
            return is_arm and has_logic_app
        except Exception:
            return False

    def parse(self, content: str) -> CacaoPlaybook:
        """Parse ARM Template JSON into a CACAO playbook."""
        data = json.loads(content)

        # Find the Logic App resource
        logic_app = None
        for resource in data.get("resources", []):
            if resource.get("type") == "Microsoft.Logic/workflows":
                logic_app = resource
                break

        if not logic_app:
            raise ValueError("No Microsoft.Logic/workflows resource found in ARM template")

        definition = logic_app.get("properties", {}).get("definition", {})
        actions = definition.get("actions", {})

        # Map action names to CACAO IDs
        action_name_to_cacao: dict[str, str] = {}
        for action_name in actions:
            action_name_to_cacao[action_name] = generate_cacao_id("action")

        # Build workflow
        workflow: dict[str, WorkflowStep] = {}
        start_id = generate_cacao_id("start")
        end_id = generate_cacao_id("end")

        # Determine execution order from runAfter
        run_after_map: dict[str, list[str]] = {}
        for action_name, action_def in actions.items():
            run_after = action_def.get("runAfter", {})
            run_after_map[action_name] = list(run_after.keys())

        # Topological sort to get execution order
        ordered_actions = self._topological_sort(actions, run_after_map)

        # Build action steps
        for i, action_name in enumerate(ordered_actions):
            action_def = actions[action_name]
            cacao_id = action_name_to_cacao[action_name]

            # Determine next step
            next_step = None
            if i + 1 < len(ordered_actions):
                next_step = action_name_to_cacao[ordered_actions[i + 1]]
            else:
                next_step = end_id

            step = self._convert_action(action_name, action_def, next_step)
            workflow[cacao_id] = step

        # Wire start
        first_action = action_name_to_cacao[ordered_actions[0]] if ordered_actions else end_id
        workflow[start_id] = WorkflowStep(
            type=WorkflowStepType.START,
            name="Start",
            on_completion=first_action,
        )
        workflow[end_id] = WorkflowStep(type=WorkflowStepType.END, name="End")

        # Extract variables from parameters
        playbook_variables = self._extract_variables(data)

        # Extract name
        name_param = data.get("parameters", {}).get("PlaybookName", {})
        playbook_name = name_param.get("defaultValue", "Imported Sentinel Playbook")
        if playbook_name.startswith("["):
            playbook_name = "Imported Sentinel Playbook"

        metadata = data.get("metadata", {})

        pb = CacaoPlaybook(
            name=metadata.get("title", playbook_name),
            description=metadata.get("description", ""),
            playbook_types=[PlaybookType.INVESTIGATION],
            workflow_start=start_id,
            workflow=workflow,
            playbook_variables=playbook_variables if playbook_variables else None,
            labels=metadata.get("tags") or None,
        )

        return pb

    def _convert_action(
        self,
        name: str,
        action_def: dict[str, Any],
        next_step: Optional[str],
    ) -> WorkflowStep:
        """Convert a Logic App action to a CACAO WorkflowStep."""
        action_type = action_def.get("type", "Compose")
        readable_name = name.replace("_", " ")

        if action_type == "If":
            # Condition step
            return WorkflowStep(
                type=WorkflowStepType.IF_CONDITION,
                name=readable_name,
                description=action_def.get("description", ""),
                condition=json.dumps(action_def.get("expression", {})),
                on_true=next_step,
                on_false=next_step,
            )

        if action_type == "Http":
            inputs = action_def.get("inputs", {})
            method = inputs.get("method", "GET")
            uri = inputs.get("uri", "/")
            body = inputs.get("body", "")
            headers = inputs.get("headers")

            return WorkflowStep(
                type=WorkflowStepType.ACTION,
                name=readable_name,
                description=action_def.get("description", ""),
                commands=[
                    Command(
                        type=CommandType.HTTP_API,
                        command=f"{method} {uri}",
                        content=body if isinstance(body, str) else json.dumps(body),
                        headers=headers if isinstance(headers, dict) else None,
                    )
                ],
                on_completion=next_step,
            )

        # Default: Compose / generic
        inputs_val = action_def.get("inputs", "")
        return WorkflowStep(
            type=WorkflowStepType.ACTION,
            name=readable_name,
            description=action_def.get("description", "") or str(inputs_val)[:200],
            commands=[
                Command(
                    type=CommandType.MANUAL,
                    command=str(inputs_val)[:500] if inputs_val else readable_name,
                )
            ],
            on_completion=next_step,
        )

    def _topological_sort(
        self,
        actions: dict[str, Any],
        run_after_map: dict[str, list[str]],
    ) -> list[str]:
        """Topological sort of actions based on runAfter dependencies."""
        visited: set[str] = set()
        result: list[str] = []
        names = list(actions.keys())

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            for dep in run_after_map.get(name, []):
                if dep in actions:
                    visit(dep)
            result.append(name)

        for name in names:
            visit(name)

        return result

    def _extract_variables(self, data: dict) -> dict[str, Variable]:
        """Extract variables from ARM template parameters."""
        variables: dict[str, Variable] = {}
        params = data.get("parameters", {})

        for name, param_def in params.items():
            if name == "PlaybookName":
                continue
            variables[name] = Variable(
                type="string",
                value=param_def.get("defaultValue", ""),
                external=True,
                description=param_def.get("metadata", {}).get("description", name),
            )

        return variables
