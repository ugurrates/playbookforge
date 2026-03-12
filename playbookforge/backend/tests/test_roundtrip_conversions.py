"""
PlaybookForge - Comprehensive Roundtrip Conversion Tests
Tests real-world XSOAR playbook import → CACAO → export to FortiSOAR/Sentinel
and reverse conversions (FortiSOAR/Sentinel → CACAO → XSOAR).

Also validates CACAO v2.0 spec compliance at every intermediate step.
"""

import json
import yaml
import pytest
from typing import Any

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
from ..core.validator import CacaoValidator, ValidationResult
from ..core.builder import PlaybookBuilder
from ..importers.xsoar_importer import XSOARImporter
from ..importers.sentinel_importer import SentinelImporter
from ..importers.fortisoar_importer import FortiSOARImporter
from ..importers.shuffle_importer import ShuffleImporter
from ..importers.auto_detect import auto_detect
from ..exporters.xsoar_exporter import XSOARExporter
from ..exporters.sentinel_fortisoar_exporter import SentinelExporter, FortiSOARExporter
from ..exporters.shuffle_exporter import ShuffleExporter


# ============================================================================
# Test Fixtures: Real-world XSOAR playbooks
# ============================================================================

XSOAR_SIMPLE_PLAYBOOK = """
id: phishing-simple
version: -1
name: "Phishing Investigation - Simple"
description: "Basic phishing email investigation"
starttaskid: "0"
tasks:
  '0':
    id: '0'
    taskid: 11111111-1111-1111-1111-111111111111
    type: start
    task:
      id: 11111111-1111-1111-1111-111111111111
      version: -1
      name: Start
      description: ""
      type: start
      iscommand: false
    nexttasks:
      '#none#':
      - '1'
    separatecontext: false
    view: '{"position":{"x":400,"y":50}}'
  '1':
    id: '1'
    taskid: 22222222-2222-2222-2222-222222222222
    type: regular
    task:
      id: 22222222-2222-2222-2222-222222222222
      version: -1
      name: "Extract Indicators"
      description: "Extract indicators from the email"
      type: regular
      iscommand: true
      script: "|||extractIndicators"
    nexttasks:
      '#none#':
      - '2'
    scriptarguments:
      text:
        simple: "${incident.labels.Email/text}"
    separatecontext: false
    view: '{"position":{"x":400,"y":200}}'
  '2':
    id: '2'
    taskid: 33333333-3333-3333-3333-333333333333
    type: condition
    task:
      id: 33333333-3333-3333-3333-333333333333
      version: -1
      name: "Is malicious?"
      description: "Check if indicators are malicious"
      type: condition
      iscommand: false
    nexttasks:
      'yes':
      - '3'
      'no':
      - '4'
    conditions:
      - label: "yes"
        condition:
          - - operator: isNotEmpty
              left:
                value:
                  simple: "${DBotScore}"
    separatecontext: false
    view: '{"position":{"x":400,"y":400}}'
  '3':
    id: '3'
    taskid: 44444444-4444-4444-4444-444444444444
    type: regular
    task:
      id: 44444444-4444-4444-4444-444444444444
      version: -1
      name: "Block Sender"
      description: "Block the sender email address"
      type: regular
      iscommand: true
      script: "|||blockSender"
    nexttasks:
      '#none#':
      - '5'
    scriptarguments:
      email:
        simple: "${incident.labels.Email/from}"
    separatecontext: false
    view: '{"position":{"x":200,"y":600}}'
  '4':
    id: '4'
    taskid: 55555555-5555-5555-5555-555555555555
    type: regular
    task:
      id: 55555555-5555-5555-5555-555555555555
      version: -1
      name: "Close as False Positive"
      description: "Close the incident as false positive"
      type: regular
      iscommand: false
    nexttasks:
      '#none#':
      - '5'
    separatecontext: false
    view: '{"position":{"x":600,"y":600}}'
  '5':
    id: '5'
    taskid: 66666666-6666-6666-6666-666666666666
    type: title
    task:
      id: 66666666-6666-6666-6666-666666666666
      version: -1
      name: "Done"
      description: ""
      type: title
      iscommand: false
    separatecontext: false
    view: '{"position":{"x":400,"y":800}}'
inputs:
  - key: Email
    value:
      simple: ""
    required: true
    description: "The suspicious email to investigate"
  - key: Threshold
    value:
      simple: "3"
    required: false
    description: "Score threshold for malicious classification"
outputs:
  - contextPath: "Phishing.Result"
    description: "The investigation result"
    type: string
tags:
  - phishing
  - email
  - investigation
fromversion: "6.0.0"
"""

XSOAR_COMPLEX_PLAYBOOK = """
id: malware-analysis-complex
version: -1
name: "Malware Analysis and Containment"
description: "Comprehensive malware analysis with sandbox detonation and containment"
starttaskid: "0"
tasks:
  '0':
    id: '0'
    taskid: a0000000-0000-0000-0000-000000000000
    type: start
    task:
      id: a0000000-0000-0000-0000-000000000000
      version: -1
      name: Start
      type: start
      iscommand: false
    nexttasks:
      '#none#':
      - '1'
    separatecontext: false
    view: '{"position":{"x":400,"y":50}}'
  '1':
    id: '1'
    taskid: a1111111-1111-1111-1111-111111111111
    type: regular
    task:
      id: a1111111-1111-1111-1111-111111111111
      version: -1
      name: "Get File Hash"
      description: "Calculate hash of the suspicious file"
      type: regular
      iscommand: true
      script: "|||hashFile"
    nexttasks:
      '#none#':
      - '2'
    scriptarguments:
      filePath:
        simple: "${incident.attachment}"
    separatecontext: false
    view: '{"position":{"x":400,"y":200}}'
  '2':
    id: '2'
    taskid: a2222222-2222-2222-2222-222222222222
    type: regular
    task:
      id: a2222222-2222-2222-2222-222222222222
      version: -1
      name: "Check VirusTotal"
      description: "Check file hash reputation on VirusTotal"
      type: regular
      iscommand: true
      script: "|||vt-file-scan"
    nexttasks:
      '#none#':
      - '3'
    scriptarguments:
      hash:
        simple: "${File.SHA256}"
    separatecontext: false
    view: '{"position":{"x":400,"y":400}}'
  '3':
    id: '3'
    taskid: a3333333-3333-3333-3333-333333333333
    type: condition
    task:
      id: a3333333-3333-3333-3333-333333333333
      version: -1
      name: "Is File Malicious?"
      description: "Check VT score against threshold"
      type: condition
      iscommand: false
    nexttasks:
      'yes':
      - '4'
      'no':
      - '7'
    conditions:
      - label: "yes"
        condition:
          - - operator: isNotEmpty
              left:
                value:
                  simple: "${VirusTotal.Detected}"
    separatecontext: false
    view: '{"position":{"x":400,"y":600}}'
  '4':
    id: '4'
    taskid: a4444444-4444-4444-4444-444444444444
    type: regular
    task:
      id: a4444444-4444-4444-4444-444444444444
      version: -1
      name: "Detonate in Sandbox"
      description: "Submit file to sandbox for dynamic analysis"
      type: regular
      iscommand: true
      script: "|||wildfire-upload"
    nexttasks:
      '#none#':
      - '5'
    scriptarguments:
      upload:
        simple: "${incident.attachment}"
    separatecontext: false
    view: '{"position":{"x":200,"y":800}}'
  '5':
    id: '5'
    taskid: a5555555-5555-5555-5555-555555555555
    type: regular
    task:
      id: a5555555-5555-5555-5555-555555555555
      version: -1
      name: "Isolate Endpoint"
      description: "Isolate the affected endpoint from network"
      type: regular
      iscommand: true
      script: "|||isolateEndpoint"
    nexttasks:
      '#none#':
      - '6'
    scriptarguments:
      hostname:
        simple: "${incident.hostname}"
    separatecontext: false
    view: '{"position":{"x":200,"y":1000}}'
  '6':
    id: '6'
    taskid: a6666666-6666-6666-6666-666666666666
    type: regular
    task:
      id: a6666666-6666-6666-6666-666666666666
      version: -1
      name: "Create Ticket"
      description: "Create incident ticket for SOC team"
      type: regular
      iscommand: true
      script: "|||createTicket"
    nexttasks:
      '#none#':
      - '8'
    scriptarguments:
      title:
        simple: "Malware Detected - ${incident.name}"
      severity:
        simple: "high"
    separatecontext: false
    view: '{"position":{"x":200,"y":1200}}'
  '7':
    id: '7'
    taskid: a7777777-7777-7777-7777-777777777777
    type: regular
    task:
      id: a7777777-7777-7777-7777-777777777777
      version: -1
      name: "Mark as Clean"
      description: "Mark file as clean, close investigation"
      type: regular
      iscommand: false
    nexttasks:
      '#none#':
      - '8'
    separatecontext: false
    view: '{"position":{"x":600,"y":1000}}'
  '8':
    id: '8'
    taskid: a8888888-8888-8888-8888-888888888888
    type: title
    task:
      id: a8888888-8888-8888-8888-888888888888
      version: -1
      name: "Complete"
      description: ""
      type: title
      iscommand: false
    separatecontext: false
    view: '{"position":{"x":400,"y":1400}}'
inputs:
  - key: FileHash
    value:
      simple: ""
    required: true
    description: "SHA256 hash of the suspicious file"
  - key: Hostname
    value:
      simple: ""
    required: true
    description: "Hostname of affected endpoint"
outputs:
  - contextPath: "Malware.Verdict"
    description: "Final malware verdict"
    type: string
  - contextPath: "Malware.SandboxReport"
    description: "Sandbox analysis report"
    type: string
tags:
  - malware
  - containment
  - sandbox
fromversion: "6.5.0"
"""


# ============================================================================
# Helper functions
# ============================================================================

def validate_cacao(playbook: CacaoPlaybook) -> ValidationResult:
    """Validate a CACAO playbook and return the result."""
    validator = CacaoValidator()
    return validator.validate(playbook)


def assert_valid_cacao(playbook: CacaoPlaybook, allow_warnings: bool = True):
    """Assert that a CACAO playbook passes validation."""
    result = validate_cacao(playbook)
    if not allow_warnings:
        assert result.valid, f"Validation failed: {[str(e) for e in result.errors]}"
    else:
        assert result.valid, f"Validation errors: {[str(e) for e in result.errors]}"


def assert_has_step_types(playbook: CacaoPlaybook, expected_types: list[WorkflowStepType]):
    """Assert that the playbook has steps of the given types."""
    actual_types = {step.type for step in playbook.workflow.values()}
    for t in expected_types:
        assert t in actual_types, f"Expected step type {t.value} not found. Got: {[t.value for t in actual_types]}"


# ============================================================================
# Test 1: XSOAR Import Tests
# ============================================================================

class TestXSOARImport:
    """Test importing XSOAR playbooks to CACAO."""

    def test_detect_xsoar_format(self):
        importer = XSOARImporter()
        assert importer.detect(XSOAR_SIMPLE_PLAYBOOK) is True
        assert importer.detect('{"not": "xsoar"}') is False
        assert importer.detect("random text") is False

    def test_import_simple_xsoar(self):
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)

        assert cacao.name == "Phishing Investigation - Simple"
        assert cacao.spec_version == "cacao-2.0"
        assert cacao.type == "playbook"
        assert cacao.id.startswith("playbook--")

        # Check workflow has start, end, and action steps
        assert_has_step_types(cacao, [
            WorkflowStepType.START,
            WorkflowStepType.ACTION,
            WorkflowStepType.IF_CONDITION,
        ])

        # Validate against CACAO spec
        assert_valid_cacao(cacao)

    def test_import_complex_xsoar(self):
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_COMPLEX_PLAYBOOK)

        assert cacao.name == "Malware Analysis and Containment"
        assert_has_step_types(cacao, [
            WorkflowStepType.START,
            WorkflowStepType.ACTION,
            WorkflowStepType.IF_CONDITION,
        ])
        assert_valid_cacao(cacao)

        # Check variables were extracted
        assert cacao.playbook_variables is not None
        assert "FileHash" in cacao.playbook_variables
        assert "Hostname" in cacao.playbook_variables

    def test_xsoar_variables_extraction(self):
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)

        assert cacao.playbook_variables is not None
        assert "Email" in cacao.playbook_variables
        assert cacao.playbook_variables["Email"].external is True
        assert "Threshold" in cacao.playbook_variables

    def test_xsoar_labels_preserved(self):
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)
        assert cacao.labels is not None
        assert "phishing" in cacao.labels

    def test_xsoar_condition_mapping(self):
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)

        # Find condition step
        cond_steps = [
            s for s in cacao.workflow.values()
            if s.type == WorkflowStepType.IF_CONDITION
        ]
        assert len(cond_steps) >= 1
        cond = cond_steps[0]
        assert cond.condition is not None
        assert cond.on_true is not None


# ============================================================================
# Test 2: XSOAR → CACAO → FortiSOAR Roundtrip
# ============================================================================

class TestXSOARToFortiSOAR:
    """Test XSOAR → CACAO → FortiSOAR conversion."""

    def test_simple_xsoar_to_fortisoar(self):
        # Step 1: Import XSOAR → CACAO
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)
        assert_valid_cacao(cacao)

        # Step 2: Export CACAO → FortiSOAR
        exporter = FortiSOARExporter()
        fsr_json = exporter.export(cacao)
        fsr = json.loads(fsr_json)

        # Validate FortiSOAR structure
        assert fsr["type"] == "workflow_collections"
        assert len(fsr["data"]) > 0
        collection = fsr["data"][0]
        assert collection["@type"] == "WorkflowCollection"
        assert len(collection["workflows"]) > 0

        workflow = collection["workflows"][0]
        assert workflow["@type"] == "Workflow"
        assert workflow["name"] == "Phishing Investigation - Simple"
        assert len(workflow["steps"]) > 0
        assert len(workflow["routes"]) > 0
        assert workflow["triggerStep"] != ""

    def test_complex_xsoar_to_fortisoar(self):
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_COMPLEX_PLAYBOOK)
        assert_valid_cacao(cacao)

        exporter = FortiSOARExporter()
        fsr_json = exporter.export(cacao)
        fsr = json.loads(fsr_json)

        workflow = fsr["data"][0]["workflows"][0]
        assert workflow["name"] == "Malware Analysis and Containment"

        # Should have steps for each CACAO step
        assert len(workflow["steps"]) >= 5

        # Check step types
        step_types = {s.get("stepType", "") for s in workflow["steps"]}
        has_condition = any("conditionStep" in st for st in step_types)
        has_execute = any("executeStep" in st for st in step_types)
        assert has_execute, f"Expected executeStep, got: {step_types}"

    def test_fortisoar_roundtrip(self):
        """XSOAR → CACAO → FortiSOAR → CACAO → verify"""
        # Forward
        xsoar_imp = XSOARImporter()
        cacao_1 = xsoar_imp.parse(XSOAR_SIMPLE_PLAYBOOK)
        assert_valid_cacao(cacao_1)

        fsr_exp = FortiSOARExporter()
        fsr_json = fsr_exp.export(cacao_1)

        # Reverse
        fsr_imp = FortiSOARImporter()
        assert fsr_imp.detect(fsr_json) is True
        cacao_2 = fsr_imp.parse(fsr_json)
        assert_valid_cacao(cacao_2)

        # Compare
        assert cacao_2.name == cacao_1.name
        assert_has_step_types(cacao_2, [WorkflowStepType.START])

        # Step count should be similar (not exact due to conversion losses)
        orig_actions = len([s for s in cacao_1.workflow.values() if s.type == WorkflowStepType.ACTION])
        rt_actions = len([s for s in cacao_2.workflow.values() if s.type == WorkflowStepType.ACTION])
        assert rt_actions >= orig_actions * 0.5, f"Too many actions lost: {orig_actions} → {rt_actions}"


# ============================================================================
# Test 3: XSOAR → CACAO → Sentinel Roundtrip
# ============================================================================

class TestXSOARToSentinel:
    """Test XSOAR → CACAO → Sentinel conversion."""

    def test_simple_xsoar_to_sentinel(self):
        # Step 1: Import XSOAR → CACAO
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)
        assert_valid_cacao(cacao)

        # Step 2: Export CACAO → Sentinel
        exporter = SentinelExporter()
        arm_json = exporter.export(cacao)
        arm = json.loads(arm_json)

        # Validate ARM Template structure
        assert "$schema" in arm
        assert "schema.management.azure.com" in arm["$schema"]
        assert "resources" in arm
        assert len(arm["resources"]) > 0

        resource = arm["resources"][0]
        assert resource["type"] == "Microsoft.Logic/workflows"
        assert "definition" in resource["properties"]

        definition = resource["properties"]["definition"]
        assert "triggers" in definition
        assert "actions" in definition
        assert "Microsoft_Sentinel_incident" in definition["triggers"]

    def test_complex_xsoar_to_sentinel(self):
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_COMPLEX_PLAYBOOK)
        assert_valid_cacao(cacao)

        exporter = SentinelExporter()
        arm_json = exporter.export(cacao)
        arm = json.loads(arm_json)

        definition = arm["resources"][0]["properties"]["definition"]
        actions = definition["actions"]
        assert len(actions) >= 3, f"Expected at least 3 actions, got {len(actions)}"

        # Check metadata
        assert arm["metadata"]["title"] == "Malware Analysis and Containment"

        # Check parameters for external variables
        params = arm["parameters"]
        assert "PlaybookName" in params

    def test_sentinel_roundtrip(self):
        """XSOAR → CACAO → Sentinel → CACAO → verify"""
        # Forward
        xsoar_imp = XSOARImporter()
        cacao_1 = xsoar_imp.parse(XSOAR_SIMPLE_PLAYBOOK)
        assert_valid_cacao(cacao_1)

        sent_exp = SentinelExporter()
        arm_json = sent_exp.export(cacao_1)

        # Reverse
        sent_imp = SentinelImporter()
        assert sent_imp.detect(arm_json) is True
        cacao_2 = sent_imp.parse(arm_json)
        assert_valid_cacao(cacao_2)

        # Compare
        assert_has_step_types(cacao_2, [WorkflowStepType.START, WorkflowStepType.ACTION])


# ============================================================================
# Test 4: FortiSOAR → CACAO → XSOAR (Reverse Direction)
# ============================================================================

class TestFortiSOARToXSOAR:
    """Test FortiSOAR → CACAO → XSOAR conversion (reverse direction)."""

    def _create_fortisoar_playbook(self) -> str:
        """Create a realistic FortiSOAR workflow JSON for testing."""
        start_uuid = "start-uuid-1111"
        step1_uuid = "step-uuid-2222"
        step2_uuid = "step-uuid-3333"
        cond_uuid = "cond-uuid-4444"
        step3_uuid = "step-uuid-5555"
        end_uuid = "end-uuid-6666"

        return json.dumps({
            "type": "workflow_collections",
            "data": [{
                "uuid": "collection-uuid",
                "@type": "WorkflowCollection",
                "name": "Incident Response Collection",
                "workflows": [{
                    "uuid": "workflow-uuid",
                    "@type": "Workflow",
                    "name": "Incident Triage and Response",
                    "description": "Automated incident triage and response workflow",
                    "isActive": True,
                    "triggerStep": start_uuid,
                    "steps": [
                        {
                            "uuid": start_uuid,
                            "@type": "WorkflowStep",
                            "name": "Start",
                            "description": "",
                            "stepType": "/api/3/workflow_step_types/startStep",
                            "arguments": {},
                        },
                        {
                            "uuid": step1_uuid,
                            "@type": "WorkflowStep",
                            "name": "Enrich Indicators",
                            "description": "Enrich IOCs with threat intelligence",
                            "stepType": "/api/3/workflow_step_types/executeStep",
                            "arguments": {
                                "connector": "cyops_utilities",
                                "operation": "api_call",
                                "operationTitle": "Threat Intel Lookup",
                                "params": {
                                    "method": "POST",
                                    "url": "https://api.threatintel.com/lookup",
                                    "body": '{"indicators": ["{{vars.input.indicators}}"]}'
                                }
                            },
                        },
                        {
                            "uuid": step2_uuid,
                            "@type": "WorkflowStep",
                            "name": "Analyze Results",
                            "description": "Parse and analyze enrichment results",
                            "stepType": "/api/3/workflow_step_types/executeStep",
                            "arguments": {
                                "connector": "cyops_utilities",
                                "operation": "execute_script",
                                "params": {
                                    "script": "import json\nresults = json.loads(input)\nreturn results['score'] > 70"
                                }
                            },
                        },
                        {
                            "uuid": cond_uuid,
                            "@type": "WorkflowStep",
                            "name": "Is Threat?",
                            "description": "Check if the threat score exceeds threshold",
                            "stepType": "/api/3/workflow_step_types/conditionStep",
                            "arguments": {
                                "conditions": [
                                    {
                                        "option": "True",
                                        "condition": "{{vars.threat_score}} > 70",
                                    },
                                    {
                                        "option": "False",
                                        "default": True,
                                    }
                                ]
                            },
                        },
                        {
                            "uuid": step3_uuid,
                            "@type": "WorkflowStep",
                            "name": "Contain Threat",
                            "description": "Block malicious IPs on firewall",
                            "stepType": "/api/3/workflow_step_types/executeStep",
                            "arguments": {
                                "connector": "cyops_utilities",
                                "operation": "api_call",
                                "operationTitle": "Block IP",
                                "params": {
                                    "method": "POST",
                                    "url": "https://firewall.local/api/block",
                                    "body": '{"ip": "{{vars.malicious_ip}}"}'
                                }
                            },
                        },
                        {
                            "uuid": end_uuid,
                            "@type": "WorkflowStep",
                            "name": "End",
                            "description": "",
                            "stepType": "/api/3/workflow_step_types/endStep",
                            "arguments": {},
                        },
                    ],
                    "routes": [
                        {"uuid": "r1", "sourceStep": start_uuid, "targetStep": step1_uuid, "label": ""},
                        {"uuid": "r2", "sourceStep": step1_uuid, "targetStep": step2_uuid, "label": ""},
                        {"uuid": "r3", "sourceStep": step2_uuid, "targetStep": cond_uuid, "label": ""},
                        {"uuid": "r4", "sourceStep": cond_uuid, "targetStep": step3_uuid, "label": "true"},
                        {"uuid": "r5", "sourceStep": cond_uuid, "targetStep": end_uuid, "label": "false"},
                        {"uuid": "r6", "sourceStep": step3_uuid, "targetStep": end_uuid, "label": ""},
                    ],
                    "tags": ["incident-response", "triage"],
                }]
            }]
        })

    def test_detect_fortisoar(self):
        importer = FortiSOARImporter()
        assert importer.detect(self._create_fortisoar_playbook()) is True

    def test_fortisoar_to_cacao(self):
        importer = FortiSOARImporter()
        cacao = importer.parse(self._create_fortisoar_playbook())

        assert cacao.name == "Incident Triage and Response"
        assert_valid_cacao(cacao)
        assert_has_step_types(cacao, [
            WorkflowStepType.START,
            WorkflowStepType.ACTION,
            WorkflowStepType.IF_CONDITION,
            WorkflowStepType.END,
        ])

    def test_fortisoar_to_xsoar(self):
        """FortiSOAR → CACAO → XSOAR"""
        fsr_imp = FortiSOARImporter()
        cacao = fsr_imp.parse(self._create_fortisoar_playbook())
        assert_valid_cacao(cacao)

        xsoar_exp = XSOARExporter()
        xsoar_yaml = xsoar_exp.export(cacao)
        xsoar = yaml.safe_load(xsoar_yaml)

        # Validate XSOAR structure
        assert "tasks" in xsoar
        assert "starttaskid" in xsoar
        assert xsoar["name"] == "Incident Triage and Response"
        assert len(xsoar["tasks"]) >= 4

        # Check task types
        task_types = {t["type"] for t in xsoar["tasks"].values()}
        assert "start" in task_types
        assert "condition" in task_types or "regular" in task_types

    def test_fortisoar_full_roundtrip(self):
        """FortiSOAR → CACAO → XSOAR → CACAO → FortiSOAR"""
        # Step 1: FortiSOAR → CACAO
        fsr_imp = FortiSOARImporter()
        cacao_1 = fsr_imp.parse(self._create_fortisoar_playbook())
        assert_valid_cacao(cacao_1)

        # Step 2: CACAO → XSOAR
        xsoar_exp = XSOARExporter()
        xsoar_yaml = xsoar_exp.export(cacao_1)

        # Step 3: XSOAR → CACAO
        xsoar_imp = XSOARImporter()
        cacao_2 = xsoar_imp.parse(xsoar_yaml)
        assert_valid_cacao(cacao_2)

        # Step 4: CACAO → FortiSOAR
        fsr_exp = FortiSOARExporter()
        fsr_json = fsr_exp.export(cacao_2)
        fsr = json.loads(fsr_json)

        assert fsr["type"] == "workflow_collections"
        assert len(fsr["data"][0]["workflows"][0]["steps"]) >= 3


# ============================================================================
# Test 5: Sentinel → CACAO → XSOAR (Reverse Direction)
# ============================================================================

class TestSentinelToXSOAR:
    """Test Sentinel → CACAO → XSOAR conversion (reverse direction)."""

    def _create_sentinel_playbook(self) -> str:
        """Create a realistic Sentinel ARM Template for testing."""
        return json.dumps({
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "metadata": {
                "title": "Block IP - Sentinel Playbook",
                "description": "Automatically block malicious IPs when a new incident is created",
                "tags": ["block-ip", "firewall", "automation"],
            },
            "parameters": {
                "PlaybookName": {
                    "defaultValue": "Block-IP-Playbook",
                    "type": "string",
                    "metadata": {"description": "Name of the Logic App / Playbook"},
                },
                "FirewallAPI": {
                    "defaultValue": "https://firewall.example.com/api",
                    "type": "string",
                    "metadata": {"description": "Firewall API endpoint"},
                },
            },
            "resources": [{
                "type": "Microsoft.Logic/workflows",
                "apiVersion": "2017-07-01",
                "name": "[parameters('PlaybookName')]",
                "location": "[resourceGroup().location]",
                "identity": {"type": "SystemAssigned"},
                "properties": {
                    "state": "Enabled",
                    "definition": {
                        "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                        "contentVersion": "1.0.0.0",
                        "triggers": {
                            "Microsoft_Sentinel_incident": {
                                "type": "ApiConnectionWebhook",
                                "inputs": {
                                    "body": {"callback_url": "@{listCallbackUrl()}"},
                                    "host": {"connection": {"name": "@parameters('$connections')['azuresentinel']['connectionId']"}},
                                    "path": "/incident-creation"
                                }
                            }
                        },
                        "actions": {
                            "Get_Incident_Entities": {
                                "type": "Http",
                                "inputs": {
                                    "method": "GET",
                                    "uri": "https://management.azure.com/api/incidents/@{triggerBody()?['object']?['properties']?['incidentNumber']}/entities",
                                },
                                "runAfter": {},
                                "description": "Get entities from the incident"
                            },
                            "Parse_IP_Addresses": {
                                "type": "Compose",
                                "inputs": "@body('Get_Incident_Entities')?['value']",
                                "runAfter": {"Get_Incident_Entities": ["Succeeded"]},
                                "description": "Extract IP addresses from entities"
                            },
                            "Check_IP_Reputation": {
                                "type": "Http",
                                "inputs": {
                                    "method": "POST",
                                    "uri": "https://api.abuseipdb.com/api/v2/check",
                                    "headers": {"Key": "api-key-placeholder"},
                                    "body": '{"ipAddress": "@{items(\'For_each_IP\')}"}'
                                },
                                "runAfter": {"Parse_IP_Addresses": ["Succeeded"]},
                                "description": "Check IP reputation via AbuseIPDB"
                            },
                            "Block_on_Firewall": {
                                "type": "Http",
                                "inputs": {
                                    "method": "POST",
                                    "uri": "[parameters('FirewallAPI')]",
                                    "body": '{"action": "block", "ip": "@{items(\'For_each_IP\')}"}'
                                },
                                "runAfter": {"Check_IP_Reputation": ["Succeeded"]},
                                "description": "Block the IP on the firewall"
                            },
                            "Add_Comment_to_Incident": {
                                "type": "Compose",
                                "inputs": "IP @{items('For_each_IP')} has been blocked on the firewall",
                                "runAfter": {"Block_on_Firewall": ["Succeeded"]},
                                "description": "Add a comment to the Sentinel incident"
                            },
                        },
                        "outputs": {},
                    },
                    "parameters": {},
                }
            }]
        })

    def test_detect_sentinel(self):
        importer = SentinelImporter()
        assert importer.detect(self._create_sentinel_playbook()) is True

    def test_sentinel_to_cacao(self):
        importer = SentinelImporter()
        cacao = importer.parse(self._create_sentinel_playbook())

        assert cacao.name == "Block IP - Sentinel Playbook"
        assert_valid_cacao(cacao)
        assert_has_step_types(cacao, [WorkflowStepType.START, WorkflowStepType.ACTION])

    def test_sentinel_to_xsoar(self):
        """Sentinel → CACAO → XSOAR"""
        sent_imp = SentinelImporter()
        cacao = sent_imp.parse(self._create_sentinel_playbook())
        assert_valid_cacao(cacao)

        xsoar_exp = XSOARExporter()
        xsoar_yaml = xsoar_exp.export(cacao)
        xsoar = yaml.safe_load(xsoar_yaml)

        assert "tasks" in xsoar
        assert xsoar["name"] == "Block IP - Sentinel Playbook"
        assert len(xsoar["tasks"]) >= 4

    def test_sentinel_to_fortisoar(self):
        """Sentinel → CACAO → FortiSOAR"""
        sent_imp = SentinelImporter()
        cacao = sent_imp.parse(self._create_sentinel_playbook())
        assert_valid_cacao(cacao)

        fsr_exp = FortiSOARExporter()
        fsr_json = fsr_exp.export(cacao)
        fsr = json.loads(fsr_json)

        assert fsr["type"] == "workflow_collections"
        workflow = fsr["data"][0]["workflows"][0]
        assert workflow["name"] == "Block IP - Sentinel Playbook"
        assert len(workflow["steps"]) >= 4

    def test_sentinel_variables_to_xsoar_inputs(self):
        """Sentinel parameters should become XSOAR inputs"""
        sent_imp = SentinelImporter()
        cacao = sent_imp.parse(self._create_sentinel_playbook())

        # FirewallAPI should be an external variable
        assert cacao.playbook_variables is not None
        assert "FirewallAPI" in cacao.playbook_variables
        assert cacao.playbook_variables["FirewallAPI"].external is True

        # Export to XSOAR and check inputs
        xsoar_exp = XSOARExporter()
        xsoar_yaml = xsoar_exp.export(cacao)
        xsoar = yaml.safe_load(xsoar_yaml)

        input_keys = [i["key"] for i in xsoar.get("inputs", [])]
        assert "FirewallAPI" in input_keys


# ============================================================================
# Test 6: Auto-detect Tests
# ============================================================================

class TestAutoDetect:
    """Test format auto-detection across all importers."""

    def test_auto_detect_xsoar(self):
        importers = [XSOARImporter(), SentinelImporter(), FortiSOARImporter(), ShuffleImporter()]
        result = auto_detect(XSOAR_SIMPLE_PLAYBOOK, importers)
        assert result is not None
        assert result.platform_id == "xsoar"

    def test_auto_detect_sentinel(self):
        importers = [XSOARImporter(), SentinelImporter(), FortiSOARImporter(), ShuffleImporter()]
        sentinel_content = TestSentinelToXSOAR()._create_sentinel_playbook()
        result = auto_detect(sentinel_content, importers)
        assert result is not None
        assert result.platform_id == "sentinel"

    def test_auto_detect_fortisoar(self):
        importers = [XSOARImporter(), SentinelImporter(), FortiSOARImporter(), ShuffleImporter()]
        fsr_content = TestFortiSOARToXSOAR()._create_fortisoar_playbook()
        result = auto_detect(fsr_content, importers)
        assert result is not None
        assert result.platform_id == "fortisoar"

    def test_auto_detect_unknown(self):
        importers = [XSOARImporter(), SentinelImporter(), FortiSOARImporter(), ShuffleImporter()]
        result = auto_detect('{"random": "data"}', importers)
        assert result is None


# ============================================================================
# Test 7: CACAO v2.0 Spec Compliance
# ============================================================================

class TestCACACOSpecCompliance:
    """Test that all conversions produce spec-compliant CACAO playbooks."""

    def test_cacao_required_fields(self):
        """Every CACAO playbook must have: type, spec_version, id, name, workflow_start, workflow"""
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)

        assert cacao.type == "playbook"
        assert cacao.spec_version == "cacao-2.0"
        assert cacao.id.startswith("playbook--")
        assert len(cacao.name) > 0
        assert cacao.workflow_start in cacao.workflow
        assert len(cacao.workflow) > 0

    def test_workflow_start_points_to_start_step(self):
        """workflow_start must point to a step with type='start'"""
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)

        start_step = cacao.workflow[cacao.workflow_start]
        assert start_step.type == WorkflowStepType.START

    def test_step_id_format(self):
        """Step IDs should follow type--uuid format"""
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)

        for step_id in cacao.workflow:
            parts = step_id.split("--")
            assert len(parts) == 2, f"Step ID '{step_id}' doesn't follow type--uuid format"

    def test_step_references_valid(self):
        """All step references must point to existing steps"""
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_COMPLEX_PLAYBOOK)

        for step_id, step in cacao.workflow.items():
            if step.on_completion:
                assert step.on_completion in cacao.workflow, f"on_completion ref '{step.on_completion}' from '{step_id}' missing"
            if step.on_success:
                assert step.on_success in cacao.workflow, f"on_success ref missing"
            if step.on_failure:
                assert step.on_failure in cacao.workflow, f"on_failure ref missing"
            if step.on_true:
                assert step.on_true in cacao.workflow, f"on_true ref missing"
            if step.on_false:
                assert step.on_false in cacao.workflow, f"on_false ref missing"

    def test_no_validation_errors(self):
        """Imported playbooks should not have validation errors"""
        for yaml_content in [XSOAR_SIMPLE_PLAYBOOK, XSOAR_COMPLEX_PLAYBOOK]:
            importer = XSOARImporter()
            cacao = importer.parse(yaml_content)
            result = validate_cacao(cacao)
            assert result.valid, f"Validation errors: {[str(e) for e in result.errors]}"

    def test_created_modified_timestamps(self):
        """created and modified timestamps must be present"""
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)
        assert cacao.created is not None
        assert cacao.modified is not None

    def test_variable_type_is_valid(self):
        """Variable types must be valid CACAO types"""
        valid_types = {"string", "integer", "long", "boolean", "float", "dictionary",
                       "list", "uuid", "ipv4-addr", "ipv6-addr", "mac-addr", "uri",
                       "sha256-hash", "md5-hash", "hex", "iban", "phone"}
        importer = XSOARImporter()
        cacao = importer.parse(XSOAR_SIMPLE_PLAYBOOK)
        if cacao.playbook_variables:
            for name, var in cacao.playbook_variables.items():
                assert var.type in valid_types, f"Invalid variable type '{var.type}' for '{name}'"


# ============================================================================
# Test 8: Cross-platform conversion matrix
# ============================================================================

class TestCrossPlatformMatrix:
    """Test all platform-to-platform conversions via CACAO."""

    def _build_test_cacao(self) -> CacaoPlaybook:
        """Build a test CACAO playbook using the builder."""
        return (
            PlaybookBuilder("Cross-Platform Test Playbook")
            .set_description("Test playbook for cross-platform conversion")
            .add_type(PlaybookType.INVESTIGATION)
            .add_label("test")
            .add_variable("target_ip", "ipv4-addr", external=True, description="Target IP")
            .add_action_step(
                name="Lookup IP Reputation",
                description="Check IP against threat intelligence",
                commands=[Command(type=CommandType.HTTP_API, command="POST /api/ti/lookup")],
            )
            .add_if_condition(
                name="Is Malicious?",
                condition="$$threat_score$$ > 70",
                on_true_name="Block IP",
                on_false_name="Log and Close",
            )
            .add_action_step(
                name="Block IP",
                description="Block the IP on the firewall",
                commands=[Command(type=CommandType.HTTP_API, command="POST /api/firewall/block")],
            )
            .add_action_step(
                name="Log and Close",
                description="Log the result and close the case",
                commands=[Command(type=CommandType.MANUAL, command="Close the case")],
            )
            .build()
        )

    def test_cacao_to_all_platforms(self):
        """Export CACAO to every platform and verify outputs are valid."""
        cacao = self._build_test_cacao()
        assert_valid_cacao(cacao)

        exporters = {
            "xsoar": XSOARExporter(),
            "sentinel": SentinelExporter(),
            "fortisoar": FortiSOARExporter(),
            "shuffle": ShuffleExporter(),
        }

        for platform, exporter in exporters.items():
            output = exporter.export(cacao)
            assert len(output) > 0, f"{platform}: empty output"

            if platform == "xsoar":
                parsed = yaml.safe_load(output)
                assert "tasks" in parsed, f"{platform}: missing tasks"
                assert "starttaskid" in parsed, f"{platform}: missing starttaskid"
            else:
                parsed = json.loads(output)
                if platform == "sentinel":
                    assert "$schema" in parsed, f"{platform}: missing $schema"
                elif platform == "fortisoar":
                    assert parsed["type"] == "workflow_collections", f"{platform}: wrong type"
                elif platform == "shuffle":
                    assert "actions" in parsed, f"{platform}: missing actions"

    def test_all_platform_roundtrips(self):
        """Test roundtrip for each platform: CACAO → Platform → CACAO."""
        cacao = self._build_test_cacao()

        roundtrip_pairs = [
            (XSOARExporter(), XSOARImporter()),
            (SentinelExporter(), SentinelImporter()),
            (FortiSOARExporter(), FortiSOARImporter()),
            (ShuffleExporter(), ShuffleImporter()),
        ]

        for exporter, importer in roundtrip_pairs:
            platform = exporter.platform_id
            # Export
            output = exporter.export(cacao)
            assert len(output) > 0, f"{platform}: empty export"

            # Import back
            assert importer.detect(output), f"{platform}: failed to detect own output"
            cacao_rt = importer.parse(output)

            # Validate
            assert_valid_cacao(cacao_rt)
            assert len(cacao_rt.workflow) >= 3, f"{platform}: too few steps after roundtrip ({len(cacao_rt.workflow)})"


# ============================================================================
# Test 9: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases in conversion."""

    def test_empty_description(self):
        """Playbook with empty description should still convert."""
        xsoar_yaml = XSOAR_SIMPLE_PLAYBOOK.replace(
            'description: "Basic phishing email investigation"',
            'description: ""'
        )
        importer = XSOARImporter()
        cacao = importer.parse(xsoar_yaml)
        assert_valid_cacao(cacao)

    def test_no_conditions(self):
        """Playbook with no conditions should convert cleanly."""
        simple = """
id: simple-no-conditions
version: -1
name: "No Conditions Playbook"
description: "Simple linear playbook"
starttaskid: "0"
tasks:
  '0':
    id: '0'
    taskid: 00000000-0000-0000-0000-000000000000
    type: start
    task:
      id: 00000000-0000-0000-0000-000000000000
      version: -1
      name: Start
      type: start
      iscommand: false
    nexttasks:
      '#none#':
      - '1'
    separatecontext: false
  '1':
    id: '1'
    taskid: 11111111-1111-1111-1111-111111111111
    type: regular
    task:
      id: 11111111-1111-1111-1111-111111111111
      version: -1
      name: "Do Something"
      description: "A single action step"
      type: regular
      iscommand: false
    separatecontext: false
inputs: []
outputs: []
tags: []
"""
        importer = XSOARImporter()
        cacao = importer.parse(simple)
        assert_valid_cacao(cacao)

        # Should export to all platforms without errors
        for exp in [XSOARExporter(), SentinelExporter(), FortiSOARExporter(), ShuffleExporter()]:
            output = exp.export(cacao)
            assert len(output) > 0

    def test_playbook_with_sub_playbook(self):
        """XSOAR playbook referencing a sub-playbook."""
        xsoar_with_sub = """
id: parent-playbook
version: -1
name: "Parent Playbook"
description: "Calls a sub-playbook"
starttaskid: "0"
tasks:
  '0':
    id: '0'
    taskid: 00000000-0000-0000-0000-000000000000
    type: start
    task:
      id: 00000000-0000-0000-0000-000000000000
      version: -1
      name: Start
      type: start
      iscommand: false
    nexttasks:
      '#none#':
      - '1'
    separatecontext: false
  '1':
    id: '1'
    taskid: 11111111-1111-1111-1111-111111111111
    type: playbook
    task:
      id: 11111111-1111-1111-1111-111111111111
      version: -1
      name: "Run Sub-Playbook"
      description: "Execute the enrichment sub-playbook"
      type: playbook
      iscommand: false
    nexttasks:
      '#none#':
      - '2'
    separatecontext: true
  '2':
    id: '2'
    taskid: 22222222-2222-2222-2222-222222222222
    type: title
    task:
      id: 22222222-2222-2222-2222-222222222222
      version: -1
      name: Done
      type: title
      iscommand: false
    separatecontext: false
inputs: []
outputs: []
tags: []
"""
        importer = XSOARImporter()
        cacao = importer.parse(xsoar_with_sub)
        assert_valid_cacao(cacao)

        # Should have a playbook-action step
        pb_action_steps = [
            s for s in cacao.workflow.values()
            if s.type == WorkflowStepType.PLAYBOOK_ACTION
        ]
        assert len(pb_action_steps) >= 1
