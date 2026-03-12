"""
PlaybookForge - FortiSOAR Importer
Converts FortiSOAR workflow_collections JSON to CACAO v2.0 format.
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


class FortiSOARImporter(BaseImporter):
    """Import FortiSOAR workflow_collections JSON to CACAO v2.0"""

    @property
    def platform_name(self) -> str:
        return "Fortinet FortiSOAR"

    @property
    def platform_id(self) -> str:
        return "fortisoar"

    @property
    def supported_extensions(self) -> list[str]:
        return [".json"]

    def detect(self, content: str) -> bool:
        """Detect FortiSOAR workflow_collections or bare Workflow format."""
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                return False
            # Standard: workflow_collections wrapper
            if data.get("type") == "workflow_collections" and "data" in data:
                return True
            # Bare workflow: @type == Workflow with steps[]
            if data.get("@type") == "Workflow" and "steps" in data:
                return True
            return False
        except Exception:
            return False

    def parse(self, content: str) -> CacaoPlaybook:
        """Parse FortiSOAR JSON into a CACAO playbook."""
        data = json.loads(content)

        # Handle bare Workflow format (@type: Workflow)
        if data.get("@type") == "Workflow" and "steps" in data:
            wf = data
            collection_name = data.get("name", "Imported FortiSOAR Workflow")
        else:
            # Standard workflow_collections wrapper
            collections = data.get("data", [])
            if not collections:
                raise ValueError("No workflow collections found")

            collection = collections[0]
            collection_name = collection.get("name", "Imported FortiSOAR Workflow")
            workflows = collection.get("workflows", [])
            if not workflows:
                raise ValueError("No workflows found in collection")

            wf = workflows[0]

        # Map FortiSOAR step UUIDs to CACAO IDs
        fsr_to_cacao: dict[str, str] = {}
        steps = wf.get("steps", [])
        routes = wf.get("routes", [])

        for step in steps:
            step_uuid = step.get("uuid", "")
            step_type = self._parse_step_type(step.get("stepType", ""))
            cacao_type = self._map_step_type(step_type)
            fsr_to_cacao[step_uuid] = generate_cacao_id(cacao_type.value)

        # Build adjacency from routes
        adjacency: dict[str, list[tuple[str, str]]] = {}
        for route in routes:
            src_raw = route.get("sourceStep", "")
            tgt_raw = route.get("targetStep", "")
            # Handle URI format: /api/3/workflow_steps/UUID
            src = src_raw.rstrip("/").split("/")[-1] if "/" in str(src_raw) else str(src_raw)
            tgt = tgt_raw.rstrip("/").split("/")[-1] if "/" in str(tgt_raw) else str(tgt_raw)
            label = route.get("label", "")
            adjacency.setdefault(src, []).append((tgt, label))

        # Build workflow steps
        workflow: dict[str, WorkflowStep] = {}

        for step in steps:
            step_uuid = step.get("uuid", "")
            cacao_id = fsr_to_cacao[step_uuid]
            step_type_str = self._parse_step_type(step.get("stepType", ""))
            cacao_type = self._map_step_type(step_type_str)

            # Get connections for this step
            connections = adjacency.get(step_uuid, [])

            kwargs: dict[str, Any] = {
                "type": cacao_type,
                "name": step.get("name", ""),
                "description": step.get("description", ""),
            }

            if cacao_type == WorkflowStepType.IF_CONDITION:
                # Map true/false from routes
                args = step.get("arguments", {})
                conditions = args.get("conditions", [])
                cond_expr = "true"
                if conditions:
                    cond_expr = conditions[0].get("condition", "true")
                kwargs["condition"] = cond_expr

                for tgt, label in connections:
                    target_cacao = fsr_to_cacao.get(tgt)
                    if label.lower() == "true" or label.lower() == "":
                        kwargs.setdefault("on_true", target_cacao)
                    if label.lower() == "false":
                        kwargs.setdefault("on_false", target_cacao)

                # Default on_true/on_false if not set
                if "on_true" not in kwargs and connections:
                    kwargs["on_true"] = fsr_to_cacao.get(connections[0][0])
                if "on_false" not in kwargs:
                    kwargs["on_false"] = kwargs.get("on_true")

            elif cacao_type == WorkflowStepType.PARALLEL:
                kwargs["next_steps"] = [
                    fsr_to_cacao.get(tgt)
                    for tgt, _ in connections
                    if fsr_to_cacao.get(tgt)
                ]
                if not kwargs["next_steps"]:
                    # Fallback: make it an action step
                    kwargs["type"] = WorkflowStepType.ACTION
                    del kwargs["next_steps"]
                    if connections:
                        kwargs["on_completion"] = fsr_to_cacao.get(connections[0][0])

            elif cacao_type not in (WorkflowStepType.END,):
                if connections:
                    kwargs["on_completion"] = fsr_to_cacao.get(connections[0][0])

            # Build commands for execute steps
            if cacao_type == WorkflowStepType.ACTION:
                kwargs["commands"] = self._build_commands(step)

            workflow[cacao_id] = WorkflowStep(**kwargs)

        # Determine workflow_start
        trigger_raw = wf.get("triggerStep", "")
        # Handle URI format: /api/3/workflow_steps/UUID
        trigger_uuid = trigger_raw.rstrip("/").split("/")[-1] if "/" in str(trigger_raw) else str(trigger_raw)
        workflow_start = fsr_to_cacao.get(trigger_uuid)

        if not workflow_start or workflow_start not in workflow:
            # Fallback: find start step
            for cid, step in workflow.items():
                if step.type == WorkflowStepType.START:
                    workflow_start = cid
                    break

        if not workflow_start:
            # Create start step
            start_id = generate_cacao_id("start")
            first = list(workflow.keys())[0] if workflow else None
            workflow[start_id] = WorkflowStep(
                type=WorkflowStepType.START,
                name="Start",
                on_completion=first,
            )
            workflow_start = start_id

        # Ensure end step
        has_end = any(s.type == WorkflowStepType.END for s in workflow.values())
        if not has_end:
            end_id = generate_cacao_id("end")
            workflow[end_id] = WorkflowStep(type=WorkflowStepType.END, name="End")

        pb = CacaoPlaybook(
            name=wf.get("name", collection_name),
            description=wf.get("description", ""),
            playbook_types=[PlaybookType.INVESTIGATION],
            workflow_start=workflow_start,
            workflow=workflow,
            labels=wf.get("tags") or None,
        )

        return pb

    # Known FortiSOAR step type UUIDs
    _STEP_TYPE_UUID_MAP: dict[str, str] = {
        "b348f017-9a94-471f-87f8-ce88b6a7ad62": "startStep",
        "04d0cf46-b6a8-42c4-8683-60a7eaa69e8f": "executeStep",  # configuration/set variable
        "0109f35d-090b-4a2b-bd8a-94cbc3508562": "executeStep",  # connector action
        "12254cf5-5db7-4b1a-8cb1-3af081924b28": "conditionStep",
        "74932bdc-b8b6-4d24-88c4-1a4dfbc524f3": "workflowStep",  # reference workflow
        "e4d9d3f2-25a8-486e-89b9-7b0e2b6a3eae": "parallelStep",
        "2597053c-e718-44b4-8394-4d40fe26d357": "endStep",
        "b593458d-3e41-46f0-b9ad-c623ac6f09a1": "executeStep",  # approval step
        "0bfed618-0316-11e7-93ae-92361f002671": "startStep",     # alt start
        "269c812b-45fc-419b-88fb-b8b1534a5aaa": "endStep",       # alt end
    }

    def _parse_step_type(self, step_type_uri: str) -> str:
        """Extract step type name from FortiSOAR URI."""
        if not step_type_uri:
            return "executeStep"
        # e.g., "/api/3/workflow_step_types/executeStep" or "/api/3/workflow_step_types/UUID"
        last_part = step_type_uri.rstrip("/").split("/")[-1]
        # Check if it's a UUID — look it up in our map
        if "-" in last_part and len(last_part) > 20:
            return self._STEP_TYPE_UUID_MAP.get(last_part, "executeStep")
        return last_part

    def _map_step_type(self, fsr_type: str) -> WorkflowStepType:
        """Map FortiSOAR step type to CACAO step type."""
        mapping = {
            "startStep": WorkflowStepType.START,
            "endStep": WorkflowStepType.END,
            "executeStep": WorkflowStepType.ACTION,
            "conditionStep": WorkflowStepType.IF_CONDITION,
            "parallelStep": WorkflowStepType.PARALLEL,
            "workflowStep": WorkflowStepType.PLAYBOOK_ACTION,
        }
        return mapping.get(fsr_type, WorkflowStepType.ACTION)

    def _build_commands(self, step: dict) -> list[Command]:
        """Build CACAO commands from FortiSOAR step arguments."""
        args = step.get("arguments", {})
        if not isinstance(args, dict):
            args = {}
        connector = args.get("connector", "")
        operation = args.get("operation", "")
        params = args.get("params", {})
        if not isinstance(params, dict):
            params = {}

        if operation == "api_call":
            method = params.get("method", "GET")
            url = params.get("url", "/")
            body = params.get("body", "")
            return [
                Command(
                    type=CommandType.HTTP_API,
                    command=f"{method} {url}",
                    content=body if body else None,
                    description=args.get("operationTitle", ""),
                )
            ]

        if operation == "execute_script":
            return [
                Command(
                    type=CommandType.BASH,
                    command=params.get("script", "echo hello"),
                )
            ]

        if operation == "no_op":
            return [
                Command(
                    type=CommandType.MANUAL,
                    command=params.get("message", step.get("name", "Manual step")),
                )
            ]

        # Generic connector operation
        return [
            Command(
                type=CommandType.HTTP_API,
                command=f"POST /api/{connector}/{operation}",
                content=json.dumps(params) if params else None,
                description=f"{connector}.{operation}",
            )
        ]
