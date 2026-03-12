#!/usr/bin/env python3
"""
PlaybookForge — Demo Script
Builds a Phishing Investigation playbook using CACAO v2.0 and exports to all supported SOAR platforms.

This demonstrates the core value proposition:
  Write ONCE in CACAO → Export to XSOAR, Shuffle, Sentinel, FortiSOAR
"""

import json
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.cacao_model import (
    CacaoPlaybook,
    Command,
    CommandType,
    PlaybookType,
    PlaybookActivityType,
    Variable,
    WorkflowStep,
    WorkflowStepType,
)
from backend.core.builder import PlaybookBuilder
from backend.core.validator import CacaoValidator
from backend.exporters import registry


def print_header(text: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_subheader(text: str) -> None:
    print(f"\n  ── {text} {'─'*(60-len(text))}\n")


def demo_build_playbook() -> CacaoPlaybook:
    """Build a comprehensive Phishing Investigation playbook"""

    print_header("STEP 1: Building CACAO Playbook with PlaybookBuilder")

    pb = (
        PlaybookBuilder("Phishing Email Investigation & Response")
        .set_description(
            "Automated investigation and response workflow for reported phishing emails. "
            "Extracts IOCs, checks reputation, and takes containment actions."
        )
        # Types & Activities
        .add_type(PlaybookType.INVESTIGATION)
        .add_type(PlaybookType.MITIGATION)
        .add_type(PlaybookType.REMEDIATION)
        .add_activity(PlaybookActivityType.IDENTIFY_IOCS)
        .add_activity(PlaybookActivityType.MATCH_INDICATORS)
        .add_activity(PlaybookActivityType.CONTAIN_SYSTEM)
        # Metadata
        .add_label("phishing")
        .add_label("email-security")
        .add_label("automated")
        .add_industry_sector("aviation")
        .set_priority(2)
        .set_severity(75)
        .set_impact(60)
        # MITRE ATT&CK
        .add_mitre_reference("T1566.001", "Spearphishing Attachment")
        .add_mitre_reference("T1566.002", "Spearphishing Link")
        .add_mitre_reference("T1204.001", "User Execution: Malicious Link")
        # Variables
        .add_variable(
            "email_id",
            var_type="string",
            external=True,
            description="The ID of the reported phishing email",
        )
        .add_variable(
            "sender_address",
            var_type="string",
            description="Extracted sender email address",
        )
        .add_variable(
            "malicious_urls",
            var_type="list",
            description="List of malicious URLs found in the email",
        )
        .add_variable(
            "verdict",
            var_type="string",
            description="Final verdict: malicious, suspicious, or clean",
        )
        .add_variable(
            "severity_score",
            var_type="integer",
            description="Calculated severity score (0-100)",
        )
        # ────── Workflow Steps ──────
        .add_action_step(
            name="Extract Email Metadata",
            description="Parse email headers, extract sender, recipient, subject, SPF/DKIM/DMARC results",
            commands=[
                Command(
                    type=CommandType.HTTP_API,
                    command="GET /api/v1/email/parse?id=$$email_id$$",
                    description="Parse email and extract metadata",
                )
            ],
            activity=PlaybookActivityType.IDENTIFY_IOCS,
        )
        .add_action_step(
            name="Extract IOCs",
            description="Extract URLs, domains, IP addresses, and file hashes from email body and attachments",
            commands=[
                Command(
                    type=CommandType.HTTP_API,
                    command="POST /api/v1/ioc/extract",
                    content='{"email_id": "$$email_id$$"}',
                    description="Extract all IOCs from email content",
                )
            ],
            activity=PlaybookActivityType.IDENTIFY_IOCS,
        )
        .add_action_step(
            name="Check URL Reputation",
            description="Query VirusTotal, URLScan.io, and internal threat intelligence for URL reputation",
            commands=[
                Command(
                    type=CommandType.HTTP_API,
                    command="POST /api/v1/reputation/url",
                    content='{"urls": "$$malicious_urls$$"}',
                    description="Multi-source URL reputation check",
                )
            ],
            activity=PlaybookActivityType.MATCH_INDICATORS,
        )
        .add_action_step(
            name="Check Sender Reputation",
            description="Verify sender domain age, WHOIS data, and historical email patterns",
            commands=[
                Command(
                    type=CommandType.HTTP_API,
                    command="POST /api/v1/reputation/sender",
                    content='{"sender": "$$sender_address$$"}',
                    description="Sender reputation analysis",
                )
            ],
            activity=PlaybookActivityType.MATCH_INDICATORS,
        )
        .add_if_condition(
            name="Is Email Malicious?",
            condition="$$verdict$$ == 'malicious'",
            on_true_name="Block Sender Domain",
            on_false_name="Update Case Status",
            description="Decision point based on aggregated threat intelligence results",
        )
        # True branch
        .add_action_step(
            name="Block Sender Domain",
            description="Add sender domain to email gateway blocklist and firewall deny list",
            commands=[
                Command(
                    type=CommandType.HTTP_API,
                    command="POST /api/v1/blocklist/domain",
                    content='{"domain": "$$sender_address$$", "source": "phishing-investigation"}',
                    description="Block sender domain on email gateway",
                )
            ],
            activity=PlaybookActivityType.DENY_ACTIVITY,
        )
        .add_action_step(
            name="Search for Other Recipients",
            description="Search email logs for other employees who received the same email",
            commands=[
                Command(
                    type=CommandType.HTTP_API,
                    command="POST /api/v1/email/search",
                    content='{"sender": "$$sender_address$$", "timeframe": "7d"}',
                    description="Find all recipients of the phishing campaign",
                )
            ],
            activity=PlaybookActivityType.INVESTIGATE_SYSTEM,
        )
        .add_action_step(
            name="Delete Phishing Emails",
            description="Purge the phishing email from all recipients' mailboxes",
            commands=[
                Command(
                    type=CommandType.HTTP_API,
                    command="POST /api/v1/email/purge",
                    content='{"email_id": "$$email_id$$", "scope": "organization"}',
                    description="Organization-wide email purge",
                )
            ],
            activity=PlaybookActivityType.CONTAIN_SYSTEM,
        )
        .add_action_step(
            name="Notify SOC Team Lead",
            description="Send notification to SOC Team Lead with investigation summary and actions taken",
            commands=[
                Command(
                    type=CommandType.MANUAL,
                    command="Send email notification to SOC Team Lead with phishing incident summary",
                )
            ],
        )
        # False branch (also reachable)
        .add_action_step(
            name="Update Case Status",
            description="Update the incident ticket with investigation findings and close if clean",
            commands=[
                Command(
                    type=CommandType.HTTP_API,
                    command="PATCH /api/v1/case/update",
                    content='{"verdict": "$$verdict$$", "severity": "$$severity_score$$"}',
                    description="Update incident case with findings",
                )
            ],
        )
        .build()
    )

    print(f"  ✅ Playbook created: {pb.name}")
    print(f"  📋 ID: {pb.id}")
    print(f"  📊 Total steps: {len(pb.workflow)}")
    print(f"  🎯 Types: {', '.join(t.value for t in pb.playbook_types)}")
    print(f"  🏷️  Labels: {', '.join(pb.labels or [])}")

    return pb


def demo_validate(playbook: CacaoPlaybook) -> None:
    """Validate the playbook"""

    print_header("STEP 2: Validating CACAO Playbook")

    validator = CacaoValidator()
    result = validator.validate(playbook)

    status = "✅ VALID" if result.valid else "❌ INVALID"
    print(f"  Status: {status}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")

    for issue in result.issues:
        icon = "❌" if issue.severity.value == "error" else "⚠️" if issue.severity.value == "warning" else "ℹ️"
        print(f"    {icon} [{issue.code}] {issue.message}")

    print(f"\n  Summary: {json.dumps(result.playbook_summary, indent=4)}")


def demo_export(playbook: CacaoPlaybook, output_dir: str) -> None:
    """Export to all platforms"""

    print_header("STEP 3: Exporting to SOAR Platforms")

    platforms = registry.list_platforms()
    print(f"  Supported platforms: {len(platforms)}")
    for p in platforms:
        print(f"    • {p['platform_name']} ({p['platform_id']}) → {p['file_extension']}")

    print()

    for platform in platforms:
        pid = platform["platform_id"]
        print_subheader(f"Exporting to {platform['platform_name']}")

        try:
            exporter = registry.get(pid)
            content = exporter.export(playbook)
            filename = exporter.get_filename(playbook)
            filepath = os.path.join(output_dir, filename)

            # Add platform prefix to avoid name collisions
            filepath = os.path.join(output_dir, f"{pid}_{filename}")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            lines = content.count("\n") + 1
            size_kb = len(content.encode()) / 1024
            print(f"  ✅ {filepath}")
            print(f"     {lines} lines, {size_kb:.1f} KB")
            print(f"     Preview (first 15 lines):")
            for line in content.split("\n")[:15]:
                print(f"       {line}")
            print(f"       ...")

        except Exception as e:
            print(f"  ❌ Failed: {e}")


def demo_cacao_json(playbook: CacaoPlaybook, output_dir: str) -> None:
    """Export raw CACAO JSON"""

    print_header("STEP 4: CACAO v2.0 JSON Output")

    cacao_json = playbook.to_json(indent=2)
    filepath = os.path.join(output_dir, "cacao_phishing_investigation.json")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(cacao_json)

    lines = cacao_json.count("\n") + 1
    size_kb = len(cacao_json.encode()) / 1024
    print(f"  ✅ {filepath}")
    print(f"     {lines} lines, {size_kb:.1f} KB")
    print(f"\n  CACAO JSON structure:")
    data = json.loads(cacao_json)
    print(f"    type: {data['type']}")
    print(f"    spec_version: {data['spec_version']}")
    print(f"    name: {data['name']}")
    print(f"    workflow_start: {data['workflow_start']}")
    print(f"    workflow steps: {len(data['workflow'])}")
    if data.get('playbook_variables'):
        print(f"    variables: {list(data['playbook_variables'].keys())}")
    if data.get('external_references'):
        print(f"    MITRE references: {len(data['external_references'])}")


def demo_cross_platform_comparison(playbook: CacaoPlaybook) -> None:
    """Show comparison of same playbook across platforms"""

    print_header("STEP 5: Cross-Platform Format Comparison")

    print("  Same playbook, 4 different formats:\n")

    # Step count comparison
    print(f"  {'Platform':<25} {'Format':<12} {'Size (KB)':<10} {'Lines':<8}")
    print(f"  {'─'*55}")

    for platform in registry.list_platforms():
        pid = platform["platform_id"]
        exporter = registry.get(pid)
        content = exporter.export(playbook)
        lines = content.count("\n") + 1
        size_kb = len(content.encode()) / 1024
        ext = platform["file_extension"]
        print(f"  {platform['platform_name']:<25} {ext:<12} {size_kb:<10.1f} {lines:<8}")

    # Also CACAO itself
    cacao_json = playbook.to_json()
    print(f"  {'CACAO v2.0 (source)':<25} {'.json':<12} {len(cacao_json.encode())/1024:<10.1f} {cacao_json.count(chr(10))+1:<8}")


def main():
    """Run the full demo"""
    print("\n" + "🔨" * 35)
    print("  PlaybookForge — Universal SOAR Playbook Converter")
    print("  Write ONCE in CACAO → Export to Any SOAR Platform")
    print("🔨" * 35)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_output")
    os.makedirs(output_dir, exist_ok=True)

    # Run demo pipeline
    playbook = demo_build_playbook()
    demo_validate(playbook)
    demo_export(playbook, output_dir)
    demo_cacao_json(playbook, output_dir)
    demo_cross_platform_comparison(playbook)

    print_header("DEMO COMPLETE")
    print(f"  📁 Output files: {output_dir}/")
    for f in sorted(os.listdir(output_dir)):
        size = os.path.getsize(os.path.join(output_dir, f))
        print(f"     • {f} ({size/1024:.1f} KB)")

    print(f"\n  🎯 1 playbook → {len(registry.list_platforms())} SOAR platforms + CACAO JSON")
    print(f"  🚀 This is what PlaybookForge does.\n")


if __name__ == "__main__":
    main()
