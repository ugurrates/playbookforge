"""
PlaybookForge - Microsoft Sentinel Exporter
Converts CACAO v2.0 playbooks to Azure ARM Template (Logic Apps) format.
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


class SentinelExporter(BaseExporter):
    """Export CACAO playbooks to Microsoft Sentinel ARM Template format"""

    @property
    def platform_name(self) -> str:
        return "Microsoft Sentinel"

    @property
    def platform_id(self) -> str:
        return "sentinel"

    @property
    def file_extension(self) -> str:
        return ".json"

    def export(self, playbook: CacaoPlaybook) -> str:
        arm = self._build_arm_template(playbook)
        return json.dumps(arm, indent=2, ensure_ascii=False)

    def _build_arm_template(self, playbook: CacaoPlaybook) -> dict[str, Any]:
        """Build Azure ARM Template for Logic App"""
        safe_name = playbook.name.replace(" ", "-").lower()[:64]

        # Build Logic App actions from CACAO workflow
        actions = {}
        run_after: dict[str, dict] = {}
        prev_action_name = None

        ordered_steps = playbook.get_steps_in_order()

        for step_id, step in ordered_steps:
            if step.type in (WorkflowStepType.START, WorkflowStepType.END):
                continue

            action_name = self._safe_action_name(step.name or f"Step_{step_id[:8]}")

            if step.type == WorkflowStepType.ACTION:
                actions[action_name] = self._build_action(step, action_name)
            elif step.type == WorkflowStepType.IF_CONDITION:
                actions[action_name] = self._build_condition(step, action_name)
            else:
                actions[action_name] = self._build_action(step, action_name)

            # Wire run_after dependencies
            if prev_action_name:
                actions[action_name]["runAfter"] = {prev_action_name: ["Succeeded"]}

            prev_action_name = action_name

        # ARM Template
        arm_template = {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "metadata": {
                "title": playbook.name,
                "description": playbook.description or "",
                "prerequisites": "Required: Microsoft Sentinel enabled workspace",
                "lastUpdateTime": playbook.modified,
                "tags": playbook.labels or [],
                "source": {
                    "kind": "Community",
                    "name": "PlaybookForge",
                },
                "support": {
                    "tier": "Community",
                },
                "_playbookforge": {
                    "source_format": "cacao-2.0",
                    "source_id": playbook.id,
                },
            },
            "parameters": {
                "PlaybookName": {
                    "defaultValue": safe_name,
                    "type": "string",
                    "metadata": {"description": "Name of the Logic App / Playbook"},
                },
                **self._build_parameters(playbook),
            },
            "variables": {},
            "resources": [
                {
                    "type": "Microsoft.Logic/workflows",
                    "apiVersion": "2017-07-01",
                    "name": "[parameters('PlaybookName')]",
                    "location": "[resourceGroup().location]",
                    "tags": {
                        "hidden-SentinelTemplateName": safe_name,
                        "hidden-SentinelTemplateVersion": "1.0",
                    },
                    "identity": {"type": "SystemAssigned"},
                    "properties": {
                        "state": "Enabled",
                        "definition": {
                            "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                            "contentVersion": "1.0.0.0",
                            "parameters": {},
                            "triggers": {
                                "Microsoft_Sentinel_incident": {
                                    "type": "ApiConnectionWebhook",
                                    "inputs": {
                                        "body": {
                                            "callback_url": "@{listCallbackUrl()}"
                                        },
                                        "host": {
                                            "connection": {
                                                "name": "@parameters('$connections')['azuresentinel']['connectionId']"
                                            }
                                        },
                                        "path": "/incident-creation",
                                    },
                                }
                            },
                            "actions": actions,
                            "outputs": {},
                        },
                        "parameters": {},
                    },
                }
            ],
        }

        return arm_template

    def _build_action(self, step: WorkflowStep, name: str) -> dict[str, Any]:
        """Build a Logic App action from a CACAO step"""
        if step.commands and step.commands[0].type == CommandType.HTTP_API:
            cmd = step.commands[0]
            parts = (cmd.command or "GET /").strip().split(maxsplit=1)
            method = parts[0] if parts else "GET"
            uri = parts[1] if len(parts) > 1 else "/"

            return {
                "type": "Http",
                "inputs": {
                    "method": method,
                    "uri": uri,
                    "headers": cmd.headers or {},
                    "body": cmd.content or "",
                },
                "runAfter": {},
                "description": step.description or "",
            }

        # Default: compose action (for manual / generic steps)
        return {
            "type": "Compose",
            "inputs": step.description or step.name or "",
            "runAfter": {},
            "description": step.description or "",
        }

    def _build_condition(self, step: WorkflowStep, name: str) -> dict[str, Any]:
        """Build a Logic App condition from a CACAO if-condition step"""
        return {
            "type": "If",
            "expression": {
                "and": [
                    {
                        "not": {"equals": [f"@{{variables('{step.condition}')}}", ""]}
                    }
                ]
            },
            "actions": {},
            "else": {"actions": {}},
            "runAfter": {},
            "description": step.description or f"Condition: {step.condition}",
        }

    def _build_parameters(self, playbook: CacaoPlaybook) -> dict[str, Any]:
        """Build ARM template parameters from CACAO variables"""
        params = {}
        if playbook.playbook_variables:
            for name, var in playbook.playbook_variables.items():
                if var.external:
                    params[name] = {
                        "type": "string",
                        "defaultValue": var.value or "",
                        "metadata": {"description": var.description or name},
                    }
        return params

    def _safe_action_name(self, name: str) -> str:
        """Convert name to valid Logic App action name"""
        safe = name.replace(" ", "_").replace("/", "_").replace("-", "_")
        return "".join(c for c in safe if c.isalnum() or c == "_")[:64]


class FortiSOARExporter(BaseExporter):
    """Export CACAO playbooks to FortiSOAR workflow JSON format"""

    @property
    def platform_name(self) -> str:
        return "Fortinet FortiSOAR"

    @property
    def platform_id(self) -> str:
        return "fortisoar"

    @property
    def file_extension(self) -> str:
        return ".json"

    def export(self, playbook: CacaoPlaybook) -> str:
        workflow = self._build_fortisoar_workflow(playbook)
        return json.dumps(workflow, indent=2, ensure_ascii=False)

    def _build_fortisoar_workflow(self, playbook: CacaoPlaybook) -> dict[str, Any]:
        """Build FortiSOAR workflow JSON"""
        steps = []
        step_id_counter = 0
        step_uuid_map: dict[str, str] = {}

        for cacao_id in playbook.workflow:
            step_uuid = str(uuid.uuid4())
            step_uuid_map[cacao_id] = step_uuid

        for cacao_id, step in playbook.workflow.items():
            fsr_step = self._convert_step(step, cacao_id, step_uuid_map, step_id_counter)
            if fsr_step:
                steps.append(fsr_step)
            step_id_counter += 1

        # Build routes (connections between steps)
        routes = []
        for cacao_id, step in playbook.workflow.items():
            src = step_uuid_map[cacao_id]
            connections = []
            if step.on_completion and step.on_completion in step_uuid_map:
                connections.append(("", step_uuid_map[step.on_completion]))
            if step.on_true and step.on_true in step_uuid_map:
                connections.append(("true", step_uuid_map[step.on_true]))
            if step.on_false and step.on_false in step_uuid_map:
                connections.append(("false", step_uuid_map[step.on_false]))
            if step.next_steps:
                for ns in step.next_steps:
                    if ns in step_uuid_map:
                        connections.append(("", step_uuid_map[ns]))

            for label, dest in connections:
                routes.append({
                    "uuid": str(uuid.uuid4()),
                    "sourceStep": src,
                    "targetStep": dest,
                    "label": label,
                    "isExecuted": False,
                })

        workflow = {
            "type": "workflow_collections",
            "data": [
                {
                    "uuid": str(uuid.uuid4()),
                    "@type": "WorkflowCollection",
                    "name": playbook.name,
                    "description": playbook.description or "",
                    "visible": True,
                    "image": None,
                    "workflows": [
                        {
                            "uuid": str(uuid.uuid4()),
                            "@type": "Workflow",
                            "name": playbook.name,
                            "description": playbook.description or "",
                            "isActive": True,
                            "debug": False,
                            "singleRecordExecution": False,
                            "priority": "/api/3/picklists/2b563c10-e7a3-4cb1-8db3-f0e7ad3c37b0",
                            "triggerStep": step_uuid_map.get(playbook.workflow_start, ""),
                            "steps": steps,
                            "routes": routes,
                            "tags": playbook.labels or [],
                            "_playbookforge_metadata": {
                                "source_format": "cacao-2.0",
                                "source_id": playbook.id,
                                "converter": "PlaybookForge",
                            },
                        }
                    ],
                }
            ],
        }

        return workflow

    def _convert_step(
        self,
        step: WorkflowStep,
        cacao_id: str,
        uuid_map: dict[str, str],
        index: int,
    ) -> dict[str, Any] | None:
        """Convert CACAO step to FortiSOAR step"""
        step_uuid = uuid_map[cacao_id]

        type_mapping = {
            WorkflowStepType.START: "startStep",
            WorkflowStepType.END: "endStep",
            WorkflowStepType.ACTION: "executeStep",
            WorkflowStepType.IF_CONDITION: "conditionStep",
            WorkflowStepType.PARALLEL: "parallelStep",
            WorkflowStepType.PLAYBOOK_ACTION: "workflowStep",
        }

        fsr_type = type_mapping.get(step.type, "executeStep")

        fsr_step: dict[str, Any] = {
            "uuid": step_uuid,
            "@type": "WorkflowStep",
            "name": step.name or f"Step {index}",
            "description": step.description or "",
            "status": None,
            "stepType": f"/api/3/workflow_step_types/{fsr_type}",
            "left": str(200 + (index % 3) * 300),
            "top": str(100 + (index // 3) * 200),
            "arguments": self._build_arguments(step, fsr_type),
        }

        return fsr_step

    def _build_arguments(self, step: WorkflowStep, fsr_type: str) -> dict[str, Any]:
        """Build FortiSOAR step arguments"""
        args: dict[str, Any] = {}

        if fsr_type == "conditionStep":
            args["conditions"] = [
                {
                    "option": "True",
                    "condition": step.condition or "",
                    "step_iri": "",
                },
                {
                    "option": "False",
                    "default": True,
                    "step_iri": "",
                },
            ]

        elif fsr_type == "executeStep" and step.commands:
            cmd = step.commands[0]
            if cmd.type == CommandType.HTTP_API:
                args["connector"] = "cyops_utilities"
                args["operation"] = "api_call"
                args["operationTitle"] = step.name or "API Call"
                args["params"] = {
                    "method": cmd.command.split()[0] if cmd.command else "GET",
                    "url": cmd.command.split()[-1] if cmd.command else "",
                    "body": cmd.content or "",
                }
            elif cmd.type in (CommandType.BASH, CommandType.SSH):
                args["connector"] = "cyops_utilities"
                args["operation"] = "execute_script"
                args["params"] = {"script": cmd.command or ""}
            elif cmd.type == CommandType.MANUAL:
                args["connector"] = "cyops_utilities"
                args["operation"] = "no_op"
                args["params"] = {"message": cmd.command or step.description or ""}

        return args
