"""
PlaybookForge - Shuffle SOAR Importer
Converts Shuffle workflow JSON to CACAO v2.0 format.
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


class ShuffleImporter(BaseImporter):
    """Import Shuffle SOAR workflow JSON to CACAO v2.0"""

    @property
    def platform_name(self) -> str:
        return "Shuffle SOAR"

    @property
    def platform_id(self) -> str:
        return "shuffle"

    @property
    def supported_extensions(self) -> list[str]:
        return [".json"]

    def detect(self, content: str) -> bool:
        """Detect Shuffle workflow format."""
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                return False
            return (
                "actions" in data
                and "triggers" in data
                and "branches" in data
            )
        except Exception:
            return False

    def parse(self, content: str) -> CacaoPlaybook:
        """Parse Shuffle JSON workflow into a CACAO playbook."""
        data = json.loads(content)

        # Map Shuffle action/trigger IDs to CACAO step IDs
        shuffle_to_cacao: dict[str, str] = {}
        workflow: dict[str, WorkflowStep] = {}

        # Process triggers → start step
        triggers = data.get("triggers") or []
        start_id = generate_cacao_id("start")
        end_id = generate_cacao_id("end")

        trigger_ids: set[str] = set()
        for trigger in triggers:
            tid = trigger.get("id", "")
            trigger_ids.add(tid)
            shuffle_to_cacao[tid] = start_id

        # Process actions → CACAO steps
        actions = data.get("actions") or []
        for action in actions:
            aid = action.get("id", "")
            cacao_id = generate_cacao_id("action")
            shuffle_to_cacao[aid] = cacao_id

        # Build adjacency from branches
        adjacency: dict[str, list[str]] = {}
        branch_labels: dict[tuple[str, str], str] = {}
        for branch in (data.get("branches") or []):
            src = branch.get("source_id", "")
            dst = branch.get("destination_id", "")
            label = branch.get("label", "")
            adjacency.setdefault(src, []).append(dst)
            if label:
                branch_labels[(src, dst)] = label

        # Create start step — find the first action to connect to
        first_action_shuffle_id = None
        # Method 1: from trigger connections
        for trigger in triggers:
            tid = trigger.get("id", "")
            if tid in adjacency:
                targets = adjacency[tid]
                if targets:
                    first_action_shuffle_id = targets[0]
                break
        # Method 2: from "start" field in workflow data
        if not first_action_shuffle_id and data.get("start"):
            first_action_shuffle_id = data["start"]
        # Method 3: from isStartNode flag on actions
        if not first_action_shuffle_id:
            for action in actions:
                if action.get("isStartNode") or action.get("is_start_node"):
                    first_action_shuffle_id = action.get("id")
                    break

        first_cacao = shuffle_to_cacao.get(first_action_shuffle_id) if first_action_shuffle_id else end_id
        workflow[start_id] = WorkflowStep(
            type=WorkflowStepType.START,
            name="Start",
            on_completion=first_cacao or end_id,
        )

        # Create action steps
        for action in actions:
            aid = action.get("id", "")
            cacao_id = shuffle_to_cacao[aid]

            # Determine step connections
            next_shuffle_ids = adjacency.get(aid, [])
            labels_for_action = {
                branch_labels.get((aid, nid), ""): nid
                for nid in next_shuffle_ids
            }

            # Check if this is a condition (has true/false branches)
            has_true = "true" in labels_for_action
            has_false = "false" in labels_for_action

            if has_true or has_false:
                # If-condition step
                on_true_id = shuffle_to_cacao.get(labels_for_action.get("true")) if has_true else end_id
                on_false_id = shuffle_to_cacao.get(labels_for_action.get("false")) if has_false else end_id
                step = WorkflowStep(
                    type=WorkflowStepType.IF_CONDITION,
                    name=action.get("label", action.get("name", "Condition")),
                    description=action.get("description", ""),
                    condition=self._extract_condition(action),
                    on_true=on_true_id or end_id,
                    on_false=on_false_id or end_id,
                )
            else:
                # Normal action step
                on_completion = None
                if next_shuffle_ids:
                    on_completion = shuffle_to_cacao.get(next_shuffle_ids[0])
                if not on_completion:
                    on_completion = end_id

                commands = self._build_commands(action)
                step = WorkflowStep(
                    type=WorkflowStepType.ACTION,
                    name=action.get("label", action.get("name", "Action")),
                    description=action.get("description", ""),
                    commands=commands,
                    on_completion=on_completion,
                )

            workflow[cacao_id] = step

        # End step
        workflow[end_id] = WorkflowStep(type=WorkflowStepType.END, name="End")

        # Build variables
        playbook_variables = self._extract_variables(data)

        pb = CacaoPlaybook(
            name=data.get("name", "Imported Shuffle Workflow"),
            description=data.get("description", ""),
            playbook_types=[PlaybookType.INVESTIGATION],
            workflow_start=start_id,
            workflow=workflow,
            playbook_variables=playbook_variables if playbook_variables else None,
            labels=data.get("tags") or None,
        )

        return pb

    def _build_commands(self, action: dict) -> list[Command]:
        """Build CACAO commands from Shuffle action."""
        app_name = action.get("app_name", "")
        action_name = action.get("name", "")
        params = action.get("parameters", [])

        # Map Shuffle apps to CACAO command types
        if app_name == "HTTP":
            method = "GET"
            url = "/"
            content = None
            for p in params:
                if p.get("name") == "method":
                    method = p.get("value", "GET")
                elif p.get("name") == "url":
                    url = p.get("value", "/")
                elif p.get("name") == "body":
                    content = p.get("value")
            return [
                Command(
                    type=CommandType.HTTP_API,
                    command=f"{method} {url}",
                    content=content,
                    description=action.get("label", ""),
                )
            ]

        if app_name in ("Shuffle Tools", "SSH"):
            cmd_value = ""
            for p in params:
                if p.get("name") in ("command", "body"):
                    cmd_value = p.get("value", "")
                    break
            cmd_type = CommandType.SSH if app_name == "SSH" else CommandType.BASH
            return [
                Command(
                    type=cmd_type,
                    command=cmd_value or action_name or "execute",
                    description=action.get("label", ""),
                )
            ]

        # Default: generic HTTP call
        return [
            Command(
                type=CommandType.HTTP_API,
                command=f"POST /api/{app_name.lower().replace(' ', '_')}/{action_name}",
                description=action.get("label", ""),
            )
        ]

    def _extract_condition(self, action: dict) -> str:
        """Extract condition string from Shuffle action parameters."""
        for p in action.get("parameters", []):
            if p.get("name") == "input_list":
                return p.get("value", "true")
        return "true"

    def _extract_variables(self, data: dict) -> dict[str, Variable]:
        """Extract variables from Shuffle workflow_variables."""
        variables: dict[str, Variable] = {}
        for var in (data.get("workflow_variables") or []):
            name = var.get("name", "")
            if name:
                variables[name] = Variable(
                    type="string",
                    value=var.get("value", ""),
                    description=var.get("description", ""),
                )
        return variables
