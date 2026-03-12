"""
PlaybookForge — Best Practices & Integration Guides Resource Catalog.

Built-in collection of SOAR integration best practices, EDR resources,
and step-by-step integration guides for security tools.
Follows the same catalog pattern as products.py.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


# ============================================================================
# Enums
# ============================================================================

class ResourceCategory(str, Enum):
    EDR = "edr"
    SIEM = "siem"
    EMAIL = "email"
    IDENTITY = "identity"
    FIREWALL = "firewall"
    THREAT_INTEL = "threat-intel"
    CLOUD = "cloud"
    INCIDENT_RESPONSE = "incident-response"
    GENERAL = "general"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class IntegrationStep:
    """A single step in an integration guide."""
    order: int
    title: str
    description: str
    code_example: str = ""

    def to_dict(self) -> dict:
        return {
            "order": self.order,
            "title": self.title,
            "description": self.description,
            "code_example": self.code_example,
        }


@dataclass
class BestPractice:
    """A SOAR best practice recommendation."""
    id: str
    title: str
    description: str
    category: ResourceCategory
    difficulty: DifficultyLevel
    steps: list[IntegrationStep] = field(default_factory=list)
    related_product_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    mitre_techniques: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "steps": [s.to_dict() for s in self.steps],
            "related_product_ids": self.related_product_ids,
            "tags": self.tags,
            "mitre_techniques": self.mitre_techniques,
            "type": "best-practice",
        }

    def to_summary(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "difficulty": self.difficulty.value,
            "step_count": len(self.steps),
            "tags": self.tags,
            "type": "best-practice",
        }


@dataclass
class IntegrationGuide:
    """A step-by-step guide for integrating a security tool with SOAR."""
    id: str
    title: str
    description: str
    category: ResourceCategory
    product_id: str
    difficulty: DifficultyLevel
    prerequisites: list[str] = field(default_factory=list)
    steps: list[IntegrationStep] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "product_id": self.product_id,
            "difficulty": self.difficulty.value,
            "prerequisites": self.prerequisites,
            "steps": [s.to_dict() for s in self.steps],
            "tags": self.tags,
            "type": "integration-guide",
        }

    def to_summary(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "product_id": self.product_id,
            "difficulty": self.difficulty.value,
            "step_count": len(self.steps),
            "tags": self.tags,
            "type": "integration-guide",
        }


# ============================================================================
# Resource Catalog
# ============================================================================

class ResourceCatalog:
    """In-memory resource catalog with search and filter."""

    def __init__(self) -> None:
        self._best_practices: dict[str, BestPractice] = {}
        self._guides: dict[str, IntegrationGuide] = {}
        self._load_builtin()

    def _load_builtin(self) -> None:
        for bp in _builtin_best_practices():
            self._best_practices[bp.id] = bp
        for g in _builtin_guides():
            self._guides[g.id] = g

    # -- Best Practices --

    def list_best_practices(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> list[BestPractice]:
        results = list(self._best_practices.values())
        if category:
            results = [bp for bp in results if bp.category.value == category]
        if difficulty:
            results = [bp for bp in results if bp.difficulty.value == difficulty]
        return results

    def get_best_practice(self, bp_id: str) -> Optional[BestPractice]:
        return self._best_practices.get(bp_id)

    # -- Integration Guides --

    def list_guides(
        self,
        category: Optional[str] = None,
        product_id: Optional[str] = None,
    ) -> list[IntegrationGuide]:
        results = list(self._guides.values())
        if category:
            results = [g for g in results if g.category.value == category]
        if product_id:
            results = [g for g in results if g.product_id == product_id]
        return results

    def get_guide(self, guide_id: str) -> Optional[IntegrationGuide]:
        return self._guides.get(guide_id)

    # -- Search --

    def search(self, query: str) -> list[dict]:
        """Search across both best practices and guides."""
        if not query.strip():
            return []
        q = query.lower()
        results: list[dict] = []

        for bp in self._best_practices.values():
            if (
                q in bp.title.lower()
                or q in bp.description.lower()
                or any(q in t.lower() for t in bp.tags)
            ):
                results.append(bp.to_summary())

        for g in self._guides.values():
            if (
                q in g.title.lower()
                or q in g.description.lower()
                or any(q in t.lower() for t in g.tags)
            ):
                results.append(g.to_summary())

        return results

    # -- EDR Resources --

    def get_edr_resources(self) -> dict:
        """Get EDR-specific resources — best practices + guides."""
        edr_bps = [
            bp for bp in self._best_practices.values()
            if bp.category == ResourceCategory.EDR
        ]
        edr_guides = [
            g for g in self._guides.values()
            if g.category == ResourceCategory.EDR
        ]
        return {
            "best_practices": [bp.to_summary() for bp in edr_bps],
            "integration_guides": [g.to_summary() for g in edr_guides],
            "total": len(edr_bps) + len(edr_guides),
        }

    # -- Categories --

    def categories(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for bp in self._best_practices.values():
            cat = bp.category.value
            counts[cat] = counts.get(cat, 0) + 1
        for g in self._guides.values():
            cat = g.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts


# ============================================================================
# Built-in Best Practices
# ============================================================================

def _builtin_best_practices() -> list[BestPractice]:
    return [
        BestPractice(
            id="bp-edr-isolation-workflow",
            title="EDR Host Isolation Workflow",
            description="Best practices for automated host isolation via EDR when malicious activity is detected. Covers pre-checks, isolation execution, notification, and post-isolation verification.",
            category=ResourceCategory.EDR,
            difficulty=DifficultyLevel.INTERMEDIATE,
            steps=[
                IntegrationStep(1, "Validate Alert Severity", "Only isolate hosts for high/critical severity alerts. Medium alerts should trigger investigation first.", "if alert.severity >= 'high':\n    proceed_to_isolation()\nelse:\n    escalate_to_analyst()"),
                IntegrationStep(2, "Check Host Criticality", "Verify host is not a critical server (DC, DNS, etc.) before isolating. Maintain a critical assets list.", "critical_assets = get_critical_asset_list()\nif host not in critical_assets:\n    proceed()\nelse:\n    require_manual_approval()"),
                IntegrationStep(3, "Execute Isolation", "Use EDR API to isolate the host. CrowdStrike: contain, Defender: isolate, SentinelOne: disconnect.", "# CrowdStrike\nPOST /devices/entities/devices-actions/v2\n{\"action_name\": \"contain\", \"ids\": [\"device_id\"]}"),
                IntegrationStep(4, "Notify SOC Team", "Send notification to SOC channel with host details, alert info, and isolation status.", "notify_soc(channel='#incidents', message=f'Host {hostname} isolated due to {alert_name}')"),
                IntegrationStep(5, "Create Incident Ticket", "Auto-create an incident ticket in ITSM with all relevant details for tracking.", "create_ticket(title=f'Host Isolation: {hostname}', priority='high', details=alert_context)"),
                IntegrationStep(6, "Post-Isolation Verification", "Verify isolation was successful by checking host network connectivity status via EDR.", "status = check_isolation_status(device_id)\nassert status == 'isolated'"),
            ],
            related_product_ids=["crowdstrike-falcon", "ms-defender-endpoint", "sentinelone"],
            tags=["edr", "isolation", "containment", "incident-response", "automation"],
            mitre_techniques=["T1059", "T1486"],
        ),
        BestPractice(
            id="bp-edr-threat-hunting",
            title="Automated Threat Hunting with EDR",
            description="Leverage EDR telemetry for automated threat hunting. Run scheduled queries, correlate with threat intel feeds, and auto-escalate findings.",
            category=ResourceCategory.EDR,
            difficulty=DifficultyLevel.ADVANCED,
            steps=[
                IntegrationStep(1, "Define Hunt Hypotheses", "Create specific hypotheses based on latest threat intel, MITRE ATT&CK TTPs, or anomalous behavior patterns."),
                IntegrationStep(2, "Build EDR Queries", "Translate hypotheses into EDR-specific queries. Use custom IOCs, behavioral patterns, or YARA rules.", "# CrowdStrike RTR\nrunscript -Raw='Get-Process | Where-Object {$_.Path -like \"*\\\\Temp\\\\*\"}'"),
                IntegrationStep(3, "Schedule Automated Scans", "Run hunt queries on a schedule (hourly/daily) and collect results for analysis."),
                IntegrationStep(4, "Correlate with Threat Intel", "Cross-reference findings with threat intelligence feeds (MISP, VirusTotal, AlienVault OTX).", "for ioc in hunt_results:\n    vt_result = check_virustotal(ioc.hash)\n    if vt_result.malicious > 5:\n        escalate(ioc)"),
                IntegrationStep(5, "Auto-Escalate Findings", "Automatically create alerts for confirmed threats and trigger response playbooks."),
            ],
            related_product_ids=["crowdstrike-falcon", "ms-defender-endpoint", "sentinelone", "virustotal"],
            tags=["edr", "threat-hunting", "proactive", "automation", "mitre"],
            mitre_techniques=["T1053", "T1105", "T1059"],
        ),
        BestPractice(
            id="bp-edr-malware-response",
            title="EDR-Driven Malware Response",
            description="Automated malware containment and remediation workflow using EDR capabilities. From detection to cleanup.",
            category=ResourceCategory.EDR,
            difficulty=DifficultyLevel.INTERMEDIATE,
            steps=[
                IntegrationStep(1, "Detect and Classify", "Use EDR detection to classify malware type (ransomware, trojan, worm, etc.) and determine blast radius."),
                IntegrationStep(2, "Isolate Affected Hosts", "Immediately contain infected endpoints via EDR network isolation."),
                IntegrationStep(3, "Collect Forensic Evidence", "Gather memory dumps, process trees, and file samples before remediation.", "# SentinelOne - Fetch file\nPOST /web/api/v2.1/agents/{id}/actions/fetch-files\n{\"data\": {\"files\": [\"/path/to/malware\"]}}"),
                IntegrationStep(4, "Remediate Threats", "Use EDR to kill processes, quarantine files, and remove persistence mechanisms."),
                IntegrationStep(5, "Scan for Lateral Movement", "Check other endpoints for IOCs associated with the detected malware."),
                IntegrationStep(6, "Restore and Monitor", "Un-isolate cleaned hosts and set up enhanced monitoring for 48-72 hours."),
            ],
            related_product_ids=["crowdstrike-falcon", "ms-defender-endpoint", "sentinelone", "carbon-black"],
            tags=["edr", "malware", "remediation", "incident-response"],
            mitre_techniques=["T1486", "T1059", "T1021"],
        ),
        BestPractice(
            id="bp-phishing-response",
            title="Phishing Email Response Automation",
            description="End-to-end automated phishing response: from user report to threat containment. Integrates email security, sandbox, and EDR.",
            category=ResourceCategory.EMAIL,
            difficulty=DifficultyLevel.INTERMEDIATE,
            steps=[
                IntegrationStep(1, "Receive Phishing Report", "Accept phishing reports via email button, Slack command, or SOC portal."),
                IntegrationStep(2, "Extract Indicators", "Parse reported email for URLs, attachments, sender info, and headers.", "indicators = extract_iocs(email)\n# URLs, hashes, sender domain, reply-to, etc."),
                IntegrationStep(3, "Check Reputation", "Look up extracted IOCs against threat intel (VirusTotal, AbuseIPDB, URLScan).", "vt_result = virustotal.scan_url(indicators.urls[0])\nif vt_result.malicious > 3:\n    mark_as_malicious()"),
                IntegrationStep(4, "Search & Purge", "Find all instances of the malicious email across mailboxes and remove them.", "# Microsoft Graph API\nPOST /security/threatIntelligence/articles/search\n{\"query\": \"sender:attacker@evil.com\"}"),
                IntegrationStep(5, "Block Sender", "Add sender domain/IP to email security blocklist."),
                IntegrationStep(6, "Check for Clicks", "Identify users who clicked malicious links and run EDR scans on their endpoints."),
                IntegrationStep(7, "Notify Users", "Send notification to affected users with guidance on password resets if needed."),
            ],
            related_product_ids=["proofpoint", "ms-defender-office", "virustotal"],
            tags=["email", "phishing", "response", "automation"],
            mitre_techniques=["T1566", "T1204"],
        ),
        BestPractice(
            id="bp-siem-alert-triage",
            title="SIEM Alert Triage Automation",
            description="Automated SIEM alert triage to reduce analyst fatigue. Enriches alerts with context, de-duplicates, and prioritizes for investigation.",
            category=ResourceCategory.SIEM,
            difficulty=DifficultyLevel.BEGINNER,
            steps=[
                IntegrationStep(1, "Receive SIEM Alert", "Configure webhook or polling to receive alerts from SIEM (Splunk, QRadar, Elastic)."),
                IntegrationStep(2, "Enrich with Context", "Add user info, asset criticality, geo-location, and historical alerts for the same entity.", "user_info = active_directory.get_user(alert.username)\nasset = cmdb.get_asset(alert.hostname)\nalert.context = {**user_info, **asset}"),
                IntegrationStep(3, "De-duplicate", "Check for similar open alerts in the last 24 hours. Merge if related."),
                IntegrationStep(4, "Calculate Priority", "Score alert based on severity, asset criticality, user role, and known threat intel."),
                IntegrationStep(5, "Route to Analyst", "Assign to appropriate SOC tier based on calculated priority and category."),
            ],
            related_product_ids=["splunk-es", "ibm-qradar", "elastic-security"],
            tags=["siem", "triage", "alert-management", "automation"],
            mitre_techniques=[],
        ),
        BestPractice(
            id="bp-identity-compromise",
            title="Identity Compromise Response",
            description="Detect and respond to compromised user accounts. Integrates IAM, SIEM, and EDR for comprehensive identity threat response.",
            category=ResourceCategory.IDENTITY,
            difficulty=DifficultyLevel.INTERMEDIATE,
            steps=[
                IntegrationStep(1, "Detect Compromise Indicators", "Monitor for impossible travel, brute force, MFA bypass, or anomalous login patterns."),
                IntegrationStep(2, "Verify with User", "Contact user through out-of-band channel to confirm activity.", "send_verification(user.phone, 'Did you login from {location}?')"),
                IntegrationStep(3, "Disable Account", "If compromise confirmed, disable account and revoke all active sessions.", "# Azure AD\nPATCH /users/{id}\n{\"accountEnabled\": false}\n\n# Revoke sessions\nPOST /users/{id}/revokeSignInSessions"),
                IntegrationStep(4, "Reset Credentials", "Force password reset and re-enroll MFA for the compromised account."),
                IntegrationStep(5, "Audit Activity", "Review all actions taken by the compromised account in the last 30 days."),
                IntegrationStep(6, "Scan Endpoints", "Run EDR scan on all devices the account accessed during compromise window."),
            ],
            related_product_ids=["azure-ad", "okta", "crowdstrike-falcon"],
            tags=["identity", "compromise", "account-takeover", "response"],
            mitre_techniques=["T1078", "T1110"],
        ),
        BestPractice(
            id="bp-firewall-block-workflow",
            title="Automated Firewall Blocking Workflow",
            description="Safely automate IP/domain blocking across firewalls. Includes validation, approval gates, and rollback procedures.",
            category=ResourceCategory.FIREWALL,
            difficulty=DifficultyLevel.BEGINNER,
            steps=[
                IntegrationStep(1, "Validate IOC", "Verify the IOC is not an internal IP, CDN, or known-good service before blocking.", "if ip in internal_ranges or ip in cdn_whitelist:\n    skip_blocking()\n    alert_analyst()"),
                IntegrationStep(2, "Check for False Positives", "Cross-reference with allow-lists and previous false positive database."),
                IntegrationStep(3, "Apply Block Rule", "Create firewall rule to block the IP/domain across all relevant firewalls.", "# Palo Alto\nPOST /api/?type=config&action=set\n&xpath=/config/devices/.../address\n&element=<entry name='blocked-{ip}'><ip-netmask>{ip}/32</ip-netmask></entry>"),
                IntegrationStep(4, "Verify Block", "Confirm the rule is active and traffic is being dropped."),
                IntegrationStep(5, "Set Expiration", "Schedule automatic rule removal after 30/60/90 days unless extended."),
                IntegrationStep(6, "Document Action", "Log the blocking action with justification for audit trail."),
            ],
            related_product_ids=["palo-alto-ngfw", "fortinet-fortigate"],
            tags=["firewall", "blocking", "containment", "automation"],
            mitre_techniques=["T1090", "T1071"],
        ),
        BestPractice(
            id="bp-vuln-prioritization",
            title="Vulnerability Prioritization & Patching",
            description="Automated vulnerability prioritization based on CVSS, exploitability, asset criticality, and threat intel context.",
            category=ResourceCategory.GENERAL,
            difficulty=DifficultyLevel.INTERMEDIATE,
            steps=[
                IntegrationStep(1, "Ingest Scan Results", "Import vulnerability scan results from scanner (Qualys, Tenable, Rapid7)."),
                IntegrationStep(2, "Enrich with Context", "Add asset criticality, business owner, and network exposure information."),
                IntegrationStep(3, "Check Exploit Availability", "Query threat intel for known exploits in the wild.", "cisa_kev = check_cisa_kev(cve_id)\nexploit_db = search_exploitdb(cve_id)\nif cisa_kev or exploit_db:\n    priority = 'critical'"),
                IntegrationStep(4, "Calculate Risk Score", "Combine CVSS, exploitability, asset value, and exposure into a risk score."),
                IntegrationStep(5, "Create Patching Tickets", "Auto-create tickets for top-priority vulnerabilities with SLA deadlines."),
                IntegrationStep(6, "Track Remediation", "Monitor patching progress and escalate overdue items."),
            ],
            related_product_ids=["tenable-io", "qualys-vmdr"],
            tags=["vulnerability", "patching", "prioritization", "risk-management"],
            mitre_techniques=["T1190"],
        ),
        BestPractice(
            id="bp-cloud-security-posture",
            title="Cloud Security Posture Monitoring",
            description="Continuously monitor cloud environments for misconfigurations and compliance violations. Auto-remediate common issues.",
            category=ResourceCategory.CLOUD,
            difficulty=DifficultyLevel.ADVANCED,
            steps=[
                IntegrationStep(1, "Enable CSPM Scanning", "Configure cloud security posture management tool to scan all accounts/subscriptions."),
                IntegrationStep(2, "Define Compliance Baselines", "Set compliance frameworks (CIS, SOC2, PCI-DSS) as baseline policies."),
                IntegrationStep(3, "Alert on Violations", "Configure real-time alerts for critical misconfigurations (public S3, open security groups).", "# AWS Config Rule\nif s3_bucket.public_access == True:\n    alert('PUBLIC_S3', bucket_name, 'critical')"),
                IntegrationStep(4, "Auto-Remediate Low Risk", "Automatically fix low-risk issues like missing encryption or logging."),
                IntegrationStep(5, "Escalate High Risk", "Route high-risk findings to cloud security team for manual review."),
            ],
            related_product_ids=["aws-security-hub", "azure-sentinel"],
            tags=["cloud", "cspm", "compliance", "automation"],
            mitre_techniques=["T1530", "T1537"],
        ),
        BestPractice(
            id="bp-incident-documentation",
            title="Automated Incident Documentation",
            description="Automatically generate incident reports and timelines from SOAR actions, reducing analyst documentation burden.",
            category=ResourceCategory.INCIDENT_RESPONSE,
            difficulty=DifficultyLevel.BEGINNER,
            steps=[
                IntegrationStep(1, "Capture All Actions", "Log every SOAR action with timestamp, actor, and result in structured format."),
                IntegrationStep(2, "Build Timeline", "Auto-generate chronological timeline from first alert to resolution."),
                IntegrationStep(3, "Collect Evidence", "Attach all relevant evidence (screenshots, logs, IOCs) to the incident record."),
                IntegrationStep(4, "Generate Report", "Use templates to create formatted incident report with executive summary, timeline, and recommendations."),
                IntegrationStep(5, "Distribute Report", "Send report to stakeholders and archive for compliance/audit purposes."),
            ],
            related_product_ids=["servicenow", "jira"],
            tags=["incident-response", "documentation", "reporting", "automation"],
            mitre_techniques=[],
        ),
        BestPractice(
            id="bp-threat-intel-enrichment",
            title="Automated Threat Intel Enrichment Pipeline",
            description="Build an automated pipeline to enrich every alert with multi-source threat intelligence, reducing MTTI (Mean Time To Investigate).",
            category=ResourceCategory.THREAT_INTEL,
            difficulty=DifficultyLevel.INTERMEDIATE,
            steps=[
                IntegrationStep(1, "Extract IOCs from Alert", "Parse alert data to extract all potential indicators (IPs, domains, hashes, URLs)."),
                IntegrationStep(2, "Query Multiple Sources", "Fan-out queries to VirusTotal, AbuseIPDB, AlienVault OTX, MISP in parallel.", "results = await asyncio.gather(\n    check_virustotal(ioc),\n    check_abuseipdb(ioc),\n    check_otx(ioc),\n    check_misp(ioc)\n)"),
                IntegrationStep(3, "Normalize & Score", "Normalize results into a unified format and calculate a composite risk score."),
                IntegrationStep(4, "Attach to Alert", "Enrich the original alert with all gathered intelligence."),
                IntegrationStep(5, "Update Local TIP", "Feed confirmed IOCs back into local threat intelligence platform for future use."),
            ],
            related_product_ids=["virustotal", "misp", "abuseipdb"],
            tags=["threat-intel", "enrichment", "automation", "ioc"],
            mitre_techniques=["T1595", "T1592"],
        ),
        BestPractice(
            id="bp-edr-policy-enforcement",
            title="EDR Policy Compliance Enforcement",
            description="Ensure all endpoints meet security policy requirements using EDR. Auto-remediate non-compliant endpoints.",
            category=ResourceCategory.EDR,
            difficulty=DifficultyLevel.BEGINNER,
            steps=[
                IntegrationStep(1, "Define Compliance Policies", "Set baseline security policies: OS patches, EDR agent version, encryption status."),
                IntegrationStep(2, "Scheduled Compliance Scans", "Run daily/weekly EDR queries to check endpoint compliance.", "# CrowdStrike - Find unpatched hosts\nGET /devices/queries/devices/v1?filter=os_version:*+platform_name:'Windows'"),
                IntegrationStep(3, "Identify Non-Compliant Hosts", "Generate list of endpoints that fail compliance checks."),
                IntegrationStep(4, "Auto-Remediate Where Possible", "Push policy updates, trigger agent updates, or enable encryption remotely."),
                IntegrationStep(5, "Report to Management", "Generate compliance dashboard and trend reports for security leadership."),
            ],
            related_product_ids=["crowdstrike-falcon", "ms-defender-endpoint", "sentinelone"],
            tags=["edr", "compliance", "policy", "enforcement"],
            mitre_techniques=[],
        ),
        BestPractice(
            id="bp-ransomware-response",
            title="Ransomware Incident Response Playbook",
            description="Critical response steps when ransomware is detected. Covers containment, assessment, recovery, and communication.",
            category=ResourceCategory.INCIDENT_RESPONSE,
            difficulty=DifficultyLevel.ADVANCED,
            steps=[
                IntegrationStep(1, "Immediate Containment", "Isolate affected endpoints via EDR. Disable affected user accounts. Block C2 IPs at firewall."),
                IntegrationStep(2, "Scope Assessment", "Determine how many endpoints are affected and what data may be encrypted.", "affected_hosts = edr.search('ransomware_note_filename')\nscope = len(affected_hosts)"),
                IntegrationStep(3, "Preserve Evidence", "Capture memory dumps and disk images before any remediation."),
                IntegrationStep(4, "Identify Ransomware Variant", "Upload samples to sandbox and check against known ransomware families.", "sample_hash = calculate_sha256(ransomware_binary)\nresult = virustotal.lookup(sample_hash)"),
                IntegrationStep(5, "Check for Decryptor", "Search No More Ransom project and vendor resources for available decryptors."),
                IntegrationStep(6, "Initiate Recovery", "Restore from backups if available. Rebuild affected systems if necessary."),
                IntegrationStep(7, "Executive Communication", "Prepare incident brief for executive team and legal counsel."),
                IntegrationStep(8, "Post-Incident Review", "Conduct lessons-learned analysis and update detection rules."),
            ],
            related_product_ids=["crowdstrike-falcon", "ms-defender-endpoint", "palo-alto-ngfw"],
            tags=["ransomware", "incident-response", "containment", "recovery"],
            mitre_techniques=["T1486", "T1490", "T1027"],
        ),
        BestPractice(
            id="bp-soar-playbook-design",
            title="SOAR Playbook Design Principles",
            description="Core principles for designing effective, maintainable SOAR playbooks. Covers modularity, error handling, and testing.",
            category=ResourceCategory.GENERAL,
            difficulty=DifficultyLevel.BEGINNER,
            steps=[
                IntegrationStep(1, "Start Simple", "Begin with the most common scenario. Add complexity only when needed."),
                IntegrationStep(2, "Use Modular Design", "Break playbooks into reusable sub-playbooks (e.g., 'Enrich IOC', 'Block IP' as modules)."),
                IntegrationStep(3, "Handle Errors Gracefully", "Every API call should have error handling. Failed steps should not crash the playbook.", "try:\n    result = api_call()\nexcept Exception as e:\n    log_error(e)\n    notify_analyst(e)\n    # Continue with degraded path"),
                IntegrationStep(4, "Add Decision Points", "Include human-in-the-loop approval for high-impact actions (isolation, account disable)."),
                IntegrationStep(5, "Test with Realistic Data", "Create test cases with real-world scenarios. Include edge cases and error conditions."),
                IntegrationStep(6, "Document Everything", "Add descriptions to every step. Future analysts need to understand the logic."),
            ],
            related_product_ids=[],
            tags=["soar", "design", "best-practices", "playbook-development"],
            mitre_techniques=[],
        ),
        BestPractice(
            id="bp-edr-forensic-collection",
            title="EDR Remote Forensic Collection",
            description="Use EDR remote response capabilities to collect forensic artifacts without physical access. Critical for distributed workforce.",
            category=ResourceCategory.EDR,
            difficulty=DifficultyLevel.ADVANCED,
            steps=[
                IntegrationStep(1, "Identify Target Endpoint", "Verify endpoint is online and EDR agent is healthy."),
                IntegrationStep(2, "Initiate Remote Session", "Start EDR real-time response session to the target endpoint.", "# CrowdStrike RTR\nPOST /real-time-response/entities/sessions/v1\n{\"device_id\": \"target_device_id\"}"),
                IntegrationStep(3, "Collect Process List", "Gather running processes, services, and network connections."),
                IntegrationStep(4, "Collect File Artifacts", "Download suspicious files, prefetch data, and browser artifacts.", "# Collect suspicious binary\nget C:\\Users\\target\\AppData\\Local\\Temp\\suspicious.exe"),
                IntegrationStep(5, "Collect Registry Keys", "Export relevant registry hives for persistence analysis."),
                IntegrationStep(6, "Memory Collection", "Capture memory dump for volatile artifact analysis."),
                IntegrationStep(7, "Package & Chain of Custody", "Hash all collected artifacts and maintain chain of custody documentation."),
            ],
            related_product_ids=["crowdstrike-falcon", "ms-defender-endpoint", "carbon-black"],
            tags=["edr", "forensics", "collection", "incident-response", "dfir"],
            mitre_techniques=["T1059", "T1547", "T1053"],
        ),
    ]


# ============================================================================
# Built-in Integration Guides
# ============================================================================

def _builtin_guides() -> list[IntegrationGuide]:
    return [
        IntegrationGuide(
            id="guide-crowdstrike-soar",
            title="CrowdStrike Falcon SOAR Integration",
            description="Step-by-step guide to integrate CrowdStrike Falcon with your SOAR platform for automated detection and response.",
            category=ResourceCategory.EDR,
            product_id="crowdstrike-falcon",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=[
                "CrowdStrike Falcon license with API access",
                "API Client ID and Secret with appropriate scopes",
                "SOAR platform with HTTP/REST connector",
            ],
            steps=[
                IntegrationStep(1, "Create API Client", "In CrowdStrike console: Support > API Clients and Keys > Add new API client. Required scopes: Detections (Read/Write), Hosts (Read/Write), Real Time Response (Read/Write).", "# Navigate to:\n# https://falcon.crowdstrike.com/support/api-clients-and-keys"),
                IntegrationStep(2, "Configure OAuth2 Token", "Use client credentials flow to obtain access tokens. Tokens expire after 30 minutes.", "POST https://api.crowdstrike.com/oauth2/token\nContent-Type: application/x-www-form-urlencoded\n\nclient_id={CLIENT_ID}&client_secret={CLIENT_SECRET}"),
                IntegrationStep(3, "Set Up Detection Webhook", "Configure CrowdStrike to send detection events to your SOAR webhook endpoint.", "# In Falcon Console: Notifications > Webhook\n# URL: https://your-soar.example.com/webhook/crowdstrike\n# Events: New Detection, Detection Update"),
                IntegrationStep(4, "Build Detection Enrichment Playbook", "Create a playbook that receives detection webhook, enriches with host info, and determines response.", "# Key API calls:\nGET /detects/entities/summaries/GET/v1  # Detection details\nGET /devices/entities/devices/v2        # Host info"),
                IntegrationStep(5, "Add Containment Actions", "Add playbook steps for host containment when severity is critical.", "POST /devices/entities/devices-actions/v2\n{\"action_name\": \"contain\", \"ids\": [\"device_id\"]}"),
                IntegrationStep(6, "Test End-to-End", "Trigger a test detection and verify the entire pipeline works: detection -> webhook -> SOAR -> enrichment -> response."),
            ],
            tags=["edr", "crowdstrike", "integration", "api", "oauth2"],
        ),
        IntegrationGuide(
            id="guide-defender-soar",
            title="Microsoft Defender for Endpoint SOAR Integration",
            description="Integrate Microsoft Defender for Endpoint with SOAR using Microsoft Graph Security API for automated threat response.",
            category=ResourceCategory.EDR,
            product_id="ms-defender-endpoint",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=[
                "Microsoft 365 E5 or Defender for Endpoint P2 license",
                "Azure AD App Registration with appropriate permissions",
                "Microsoft Graph API permissions: SecurityEvents.ReadWrite.All, Machine.Isolate, Machine.Scan",
            ],
            steps=[
                IntegrationStep(1, "Register Azure AD Application", "Create app registration in Azure Portal for SOAR integration.", "# Azure Portal > Azure Active Directory > App Registrations\n# Redirect URI: https://your-soar/callback\n# API Permissions: Microsoft Graph > SecurityEvents.ReadWrite.All"),
                IntegrationStep(2, "Configure Authentication", "Set up client credentials or delegated auth flow for API access.", "POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token\ngrant_type=client_credentials\n&client_id={APP_ID}\n&client_secret={SECRET}\n&scope=https://graph.microsoft.com/.default"),
                IntegrationStep(3, "Set Up Alert Streaming", "Configure Microsoft 365 Defender to stream alerts to your SOAR.", "# Use Microsoft Graph Security API\nGET /security/alerts_v2?$filter=status eq 'new'"),
                IntegrationStep(4, "Build Response Playbook", "Create playbook with isolation, scan, and evidence collection actions.", "# Isolate machine\nPOST /security/tiIndicators\n\n# Run AV scan\nPOST /security/tiIndicators/{id}/runAntiVirusScan"),
                IntegrationStep(5, "Add Logic App Connector", "For Sentinel users, leverage built-in Logic App connectors for seamless integration."),
                IntegrationStep(6, "Validate with Test Alert", "Generate a test alert using EICAR file and verify end-to-end flow."),
            ],
            tags=["edr", "microsoft", "defender", "graph-api", "azure"],
        ),
        IntegrationGuide(
            id="guide-sentinelone-soar",
            title="SentinelOne SOAR Integration",
            description="Connect SentinelOne to your SOAR platform for automated endpoint threat detection, isolation, and remediation.",
            category=ResourceCategory.EDR,
            product_id="sentinelone",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=[
                "SentinelOne Complete or above license",
                "API Token with appropriate permissions",
                "SOAR platform with REST API connector",
            ],
            steps=[
                IntegrationStep(1, "Generate API Token", "In SentinelOne console: Settings > Users > API Token. Generate token with appropriate scope.", "# Navigate to: https://your-tenant.sentinelone.net\n# Settings > Users > Your User > API Token > Generate"),
                IntegrationStep(2, "Configure SOAR Connector", "Set up REST connector in your SOAR with SentinelOne base URL and API token.", "Base URL: https://your-tenant.sentinelone.net/web/api/v2.1\nHeaders: Authorization: ApiToken {YOUR_TOKEN}"),
                IntegrationStep(3, "Set Up Threat Webhooks", "Configure SentinelOne to send threat notifications to SOAR.", "# Notifications > Webhook\n# URL: https://your-soar/webhook/sentinelone"),
                IntegrationStep(4, "Build Detection Playbook", "Create playbook for auto-enrichment and classification of S1 threats.", "GET /threats?limit=10&sortBy=createdAt&sortOrder=desc"),
                IntegrationStep(5, "Add Response Actions", "Implement isolation, remediation, and rollback actions.", "# Disconnect from network\nPOST /agents/actions/disconnect\n{\"filter\": {\"ids\": [\"agent_id\"]}}"),
                IntegrationStep(6, "Enable Deep Visibility Queries", "Leverage S1 Deep Visibility for threat hunting from SOAR.", "POST /dv/init-query\n{\"query\": \"ObjectType = 'process' AND TgtFileSHA256 = '{hash}'\"}"),
            ],
            tags=["edr", "sentinelone", "integration", "api"],
        ),
        IntegrationGuide(
            id="guide-splunk-soar",
            title="Splunk Enterprise Security SOAR Integration",
            description="Connect Splunk ES with SOAR for automated alert triage, investigation, and response using Splunk's REST API.",
            category=ResourceCategory.SIEM,
            product_id="splunk-es",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=[
                "Splunk Enterprise Security license",
                "Splunk REST API access (port 8089)",
                "Service account with appropriate roles",
            ],
            steps=[
                IntegrationStep(1, "Create Service Account", "Create a Splunk user with 'ess_analyst' role for API access.", "# Splunk Web > Settings > Users > New User\n# Role: ess_analyst, can_delete=false"),
                IntegrationStep(2, "Configure REST Connector", "Set up connection to Splunk REST API in your SOAR platform.", "Base URL: https://splunk-server:8089\nAuth: Basic (service_account:password)\nVerify SSL: true"),
                IntegrationStep(3, "Build Notable Event Ingestion", "Create polling mechanism to fetch notable events from ES.", "POST /services/search/jobs\nsearch=| `notable` | where status=\"new\" | head 50"),
                IntegrationStep(4, "Auto-Enrich Notables", "Enrich each notable event with asset and identity lookups from Splunk.", "POST /services/search/jobs\nsearch=| inputlookup asset_lookup_by_str where key=\"{src_ip}\""),
                IntegrationStep(5, "Implement Response Actions", "Add adaptive response actions back to Splunk ES.", "POST /services/notable_update\n{\"ruleUIDs\": [\"notable_id\"], \"status\": \"2\", \"comment\": \"Auto-triaged by SOAR\"}"),
                IntegrationStep(6, "Create Dashboard", "Build Splunk dashboard showing SOAR automation metrics and response times."),
            ],
            tags=["siem", "splunk", "integration", "notable-events"],
        ),
        IntegrationGuide(
            id="guide-paloalto-soar",
            title="Palo Alto NGFW SOAR Integration",
            description="Integrate Palo Alto Networks NGFW with SOAR for automated threat blocking, policy management, and traffic analysis.",
            category=ResourceCategory.FIREWALL,
            product_id="palo-alto-ngfw",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=[
                "PAN-OS 9.0+ with API access enabled",
                "API Key with appropriate admin privileges",
                "SOAR platform with XML/REST connector",
            ],
            steps=[
                IntegrationStep(1, "Generate API Key", "Generate an API key from the Palo Alto firewall.", "GET https://firewall/api/?type=keygen&user={ADMIN_USER}&password={ADMIN_PASS}\n# Returns: <response><result><key>YOUR_API_KEY</key></result></response>"),
                IntegrationStep(2, "Configure SOAR Connector", "Set up Palo Alto connector with firewall IP and API key.", "Base URL: https://firewall-ip/api/\nAPI Key: {YOUR_API_KEY}\nVerify SSL: true"),
                IntegrationStep(3, "Create Address Objects", "Build playbook to dynamically create address objects for blocking.", "POST /api/?type=config&action=set\n&xpath=/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/address\n&element=<entry name='blocked-{ip}'><ip-netmask>{ip}/32</ip-netmask><description>Blocked by SOAR</description></entry>"),
                IntegrationStep(4, "Update Security Rules", "Add blocked addresses to deny rules or EDL (External Dynamic List).", "# Recommended: Use EDL for dynamic blocking\n# Configure EDL on PAN-OS pointing to SOAR-hosted list"),
                IntegrationStep(5, "Commit Changes", "Auto-commit configuration changes after rule updates.", "POST /api/?type=commit&cmd=<commit><description>SOAR auto-block</description></commit>"),
                IntegrationStep(6, "Monitor Traffic Logs", "Query traffic logs to verify blocks and identify blocked traffic patterns.", "POST /api/?type=log&log-type=traffic&query=(addr.src in blocked-ips)"),
            ],
            tags=["firewall", "palo-alto", "blocking", "integration"],
        ),
        IntegrationGuide(
            id="guide-virustotal-soar",
            title="VirusTotal SOAR Integration",
            description="Integrate VirusTotal API with SOAR for automated IOC reputation checking and file/URL scanning.",
            category=ResourceCategory.THREAT_INTEL,
            product_id="virustotal",
            difficulty=DifficultyLevel.BEGINNER,
            prerequisites=[
                "VirusTotal API key (free or premium)",
                "SOAR platform with REST connector",
                "Understanding of API rate limits (free: 4 req/min)",
            ],
            steps=[
                IntegrationStep(1, "Obtain API Key", "Sign up at virustotal.com and get your API key from the profile page.", "# API Key location:\n# https://www.virustotal.com/gui/my-apikey"),
                IntegrationStep(2, "Configure Rate Limiting", "Set up rate limiting in your SOAR to respect API quotas.", "# Free tier: 4 requests/minute, 500/day, 15.5K/month\n# Premium: Higher limits based on subscription"),
                IntegrationStep(3, "Build Hash Lookup Playbook", "Create reusable sub-playbook for file hash reputation checks.", "GET https://www.virustotal.com/api/v3/files/{hash}\nHeaders: x-apikey: {API_KEY}\n\n# Check: data.attributes.last_analysis_stats.malicious > 5"),
                IntegrationStep(4, "Build URL Scan Playbook", "Create sub-playbook for URL scanning and reputation.", "POST https://www.virustotal.com/api/v3/urls\nHeaders: x-apikey: {API_KEY}\nBody: url={encoded_url}"),
                IntegrationStep(5, "Build IP Reputation Playbook", "Create sub-playbook for IP address reputation lookup.", "GET https://www.virustotal.com/api/v3/ip_addresses/{ip}\n# Check: data.attributes.last_analysis_stats"),
                IntegrationStep(6, "Integrate with Alert Pipeline", "Wire VT lookups into your main alert triage playbook for automatic enrichment."),
            ],
            tags=["threat-intel", "virustotal", "ioc", "reputation", "api"],
        ),
        IntegrationGuide(
            id="guide-servicenow-soar",
            title="ServiceNow ITSM SOAR Integration",
            description="Connect ServiceNow with SOAR for automated incident ticket creation, updates, and bi-directional sync.",
            category=ResourceCategory.INCIDENT_RESPONSE,
            product_id="servicenow",
            difficulty=DifficultyLevel.BEGINNER,
            prerequisites=[
                "ServiceNow instance with REST API enabled",
                "Service account with incident table access",
                "SOAR platform with REST connector",
            ],
            steps=[
                IntegrationStep(1, "Create Integration User", "Create a dedicated service account in ServiceNow for SOAR integration.", "# Navigate to: User Administration > Users > New\n# Role: itil, rest_api_explorer\n# Active: true"),
                IntegrationStep(2, "Configure REST Connector", "Set up connection to ServiceNow Table API.", "Base URL: https://instance.service-now.com/api/now\nAuth: Basic (integration_user:password)\nContent-Type: application/json"),
                IntegrationStep(3, "Build Incident Creation Playbook", "Create playbook step to auto-create incidents from security alerts.", "POST /api/now/table/incident\n{\n  \"short_description\": \"Security Alert: {alert_title}\",\n  \"urgency\": \"1\",\n  \"impact\": \"2\",\n  \"category\": \"security\",\n  \"description\": \"{alert_details}\"\n}"),
                IntegrationStep(4, "Add Bi-Directional Sync", "Update SOAR case when ServiceNow ticket is updated and vice versa.", "# Webhook from ServiceNow Business Rule\n# Or: Poll for updates\nGET /api/now/table/incident/{sys_id}"),
                IntegrationStep(5, "Map Priority Levels", "Create mapping between SOAR severity and ServiceNow priority/urgency."),
                IntegrationStep(6, "Test with Sample Incident", "Create a test security incident and verify the full lifecycle."),
            ],
            tags=["itsm", "servicenow", "ticketing", "integration", "incident"],
        ),
        IntegrationGuide(
            id="guide-azure-sentinel-soar",
            title="Microsoft Sentinel SOAR Integration",
            description="Leverage Azure Logic Apps and Sentinel's built-in SOAR capabilities for automated incident response.",
            category=ResourceCategory.SIEM,
            product_id="azure-sentinel",
            difficulty=DifficultyLevel.ADVANCED,
            prerequisites=[
                "Microsoft Sentinel workspace",
                "Azure subscription with Logic Apps access",
                "Managed Identity or Service Principal for API access",
            ],
            steps=[
                IntegrationStep(1, "Enable Automation Rules", "Configure Sentinel automation rules to trigger playbooks on incident creation.", "# Sentinel > Automation > Create Rule\n# Trigger: When incident is created\n# Condition: Severity >= Medium\n# Action: Run playbook"),
                IntegrationStep(2, "Create Logic App Playbook", "Build a Logic App that responds to Sentinel incident triggers.", "# Trigger: Microsoft Sentinel Incident\n# Get: Incident entities (IPs, accounts, hosts)\n# Action: Enrich with threat intel"),
                IntegrationStep(3, "Add Entity Enrichment", "Enrich incident entities using Microsoft Graph and external APIs.", "# Get user info\nGET https://graph.microsoft.com/v1.0/users/{upn}\n\n# Get device info\nGET https://graph.microsoft.com/v1.0/devices?$filter=displayName eq '{hostname}'"),
                IntegrationStep(4, "Implement Response Actions", "Add response actions like disabling users, isolating machines, or blocking IPs.", "# Disable user account\nPATCH https://graph.microsoft.com/v1.0/users/{id}\n{\"accountEnabled\": false}"),
                IntegrationStep(5, "Update Incident", "Close or update the Sentinel incident with findings and actions taken.", "# Update incident status\nPUT /incidents/{id}\n{\"properties\": {\"status\": \"Closed\", \"classification\": \"TruePositive\"}}"),
                IntegrationStep(6, "Monitor Playbook Runs", "Track playbook execution in Sentinel > Automation > Playbook runs."),
            ],
            tags=["siem", "sentinel", "logic-apps", "azure", "automation"],
        ),
        IntegrationGuide(
            id="guide-okta-soar",
            title="Okta Identity SOAR Integration",
            description="Integrate Okta with SOAR for automated identity threat response: account suspension, MFA reset, and session revocation.",
            category=ResourceCategory.IDENTITY,
            product_id="okta",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisites=[
                "Okta organization with API access",
                "API Token with Super Admin or appropriate privileges",
                "SOAR platform with REST connector",
            ],
            steps=[
                IntegrationStep(1, "Create API Token", "Generate API token in Okta Admin Console.", "# Security > API > Tokens > Create Token\n# Name: SOAR-Integration\n# Copy the token immediately (shown only once)"),
                IntegrationStep(2, "Configure SOAR Connector", "Set up REST connector with Okta API.", "Base URL: https://your-org.okta.com/api/v1\nHeaders: Authorization: SSWS {API_TOKEN}\nContent-Type: application/json"),
                IntegrationStep(3, "Build User Lookup Playbook", "Create sub-playbook to look up user details by email or username.", "GET /api/v1/users/{login}\n# Returns: user profile, status, MFA factors, groups"),
                IntegrationStep(4, "Implement Suspend Action", "Add ability to suspend compromised accounts.", "POST /api/v1/users/{userId}/lifecycle/suspend"),
                IntegrationStep(5, "Add MFA Reset", "Reset MFA factors for compromised accounts.", "DELETE /api/v1/users/{userId}/factors/{factorId}"),
                IntegrationStep(6, "Revoke Sessions", "Clear all active sessions for a compromised user.", "DELETE /api/v1/users/{userId}/sessions"),
            ],
            tags=["identity", "okta", "iam", "integration", "mfa"],
        ),
    ]


# ============================================================================
# Global Singleton
# ============================================================================

resource_catalog = ResourceCatalog()
