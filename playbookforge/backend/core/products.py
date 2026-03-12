"""
PlaybookForge - Vendor Security Product Catalog

Defines 26 security products across 11 categories with realistic API actions.
Each product includes common operations used in SOAR playbooks (block IP, isolate host,
lookup hash, etc.) with real endpoint patterns and parameters.

Used by:
- Designer: command/action selection when building playbook steps
- AI/LLM: product-aware playbook generation (n8n-style)
- Frontend: product picker components
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .cacao_model import PlaybookActivityType


# ============================================================================
# Enums
# ============================================================================

class ProductCategory(str, Enum):
    FIREWALL = "firewall"
    EDR_XDR = "edr-xdr"
    SIEM = "siem"
    EMAIL_SECURITY = "email-security"
    WAF = "waf"
    IDENTITY_IAM = "identity-iam"
    THREAT_INTEL = "threat-intel"
    VULN_MANAGEMENT = "vulnerability-management"
    CLOUD_SECURITY = "cloud-security"
    ENDPOINT_MGMT = "endpoint-management"
    TICKETING = "ticketing"


class AuthType(str, Enum):
    API_KEY = "api-key"
    OAUTH2 = "oauth2"
    BASIC = "basic-auth"
    BEARER = "bearer-token"
    CERTIFICATE = "certificate"


# ============================================================================
# Data Models
# ============================================================================

class ActionParameter(BaseModel):
    """A parameter for a product action."""
    name: str
    type: str = "string"  # string, ipv4-addr, ipv6-addr, hash, url, integer, boolean, list
    required: bool = True
    description: str = ""
    example: Optional[str] = None


class ProductAction(BaseModel):
    """A single API action that a security product can perform."""
    id: str
    name: str
    description: str
    http_method: str = "POST"
    endpoint_pattern: str = ""
    parameters: list[ActionParameter] = Field(default_factory=list)
    cacao_activity: Optional[PlaybookActivityType] = None


class Product(BaseModel):
    """A vendor security product with its API actions."""
    id: str
    name: str
    vendor: str
    category: ProductCategory
    description: str
    auth_types: list[AuthType] = Field(default_factory=list)
    base_url_pattern: str = ""
    actions: list[ProductAction] = Field(default_factory=list)
    logo_abbr: str = ""
    logo_color: str = "bg-slate-600"


# ============================================================================
# Product Catalog
# ============================================================================

class ProductCatalog:
    """In-memory product catalog with search and filter."""

    def __init__(self) -> None:
        self._products: dict[str, Product] = {}
        self._load_builtin()

    def _load_builtin(self) -> None:
        for p in _builtin_products():
            self._products[p.id] = p

    def list_all(self, category: Optional[str] = None) -> list[Product]:
        products = list(self._products.values())
        if category:
            products = [p for p in products if p.category.value == category]
        return sorted(products, key=lambda p: (p.category.value, p.vendor, p.name))

    def get(self, product_id: str) -> Optional[Product]:
        return self._products.get(product_id)

    def search(self, query: str) -> list[Product]:
        q = query.lower()
        results = []
        for p in self._products.values():
            if (q in p.name.lower() or q in p.vendor.lower()
                    or q in p.category.value.lower() or q in p.description.lower()):
                results.append(p)
        return sorted(results, key=lambda p: p.name)

    def categories(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for p in self._products.values():
            cat = p.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return dict(sorted(counts.items()))

    def get_actions_for_products(self, product_ids: list[str]) -> dict[str, list[dict]]:
        result: dict[str, list[dict]] = {}
        for pid in product_ids:
            product = self._products.get(pid)
            if product:
                result[pid] = [a.model_dump() for a in product.actions]
        return result

    def count(self) -> int:
        return len(self._products)


# ============================================================================
# Built-in Product Definitions (26 Products)
# ============================================================================

def _p(name: str, type: str = "string", required: bool = True,
       desc: str = "", example: str = "") -> ActionParameter:
    """Shorthand for creating ActionParameter."""
    return ActionParameter(name=name, type=type, required=required,
                           description=desc, example=example)


def _builtin_products() -> list[Product]:
    """Return all 26 built-in security products."""
    return [
        # ================================================================
        # FIREWALL / NGFW (4)
        # ================================================================
        Product(
            id="paloalto_ngfw",
            name="Palo Alto Networks NGFW",
            vendor="Palo Alto Networks",
            category=ProductCategory.FIREWALL,
            description="Next-Generation Firewall with advanced threat prevention, URL filtering, and application control.",
            auth_types=[AuthType.API_KEY],
            base_url_pattern="https://{firewall_host}/api",
            logo_abbr="PA",
            logo_color="bg-red-600",
            actions=[
                ProductAction(
                    id="block_ip", name="Block IP Address",
                    description="Add an IP address to the block list / deny rule on the firewall.",
                    http_method="POST", endpoint_pattern="/v1/security/rules",
                    cacao_activity=PlaybookActivityType.DENY_ACTIVITY,
                    parameters=[
                        _p("ip_address", "ipv4-addr", desc="IP address to block", example="10.0.0.1"),
                        _p("rule_name", desc="Name for the security rule", example="Block-Malicious-IP"),
                        _p("direction", required=False, desc="Traffic direction: inbound/outbound/both", example="both"),
                    ],
                ),
                ProductAction(
                    id="unblock_ip", name="Unblock IP Address",
                    description="Remove an IP address from the block list.",
                    http_method="DELETE", endpoint_pattern="/v1/security/rules/{rule_id}",
                    cacao_activity=PlaybookActivityType.ALLOW_ACTIVITY,
                    parameters=[
                        _p("ip_address", "ipv4-addr", desc="IP address to unblock"),
                        _p("rule_id", desc="Rule ID to delete"),
                    ],
                ),
                ProductAction(
                    id="create_address_object", name="Create Address Object",
                    description="Create a new address object for use in security policies.",
                    http_method="POST", endpoint_pattern="/v1/objects/addresses",
                    parameters=[
                        _p("name", desc="Object name", example="Malicious-Host-1"),
                        _p("ip_netmask", desc="IP/CIDR", example="192.168.1.0/24"),
                        _p("description", required=False, desc="Object description"),
                    ],
                ),
                ProductAction(
                    id="get_traffic_logs", name="Get Traffic Logs",
                    description="Retrieve firewall traffic logs filtered by source/destination.",
                    http_method="GET", endpoint_pattern="/v1/logs/traffic",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("source_ip", "ipv4-addr", required=False, desc="Filter by source IP"),
                        _p("dest_ip", "ipv4-addr", required=False, desc="Filter by destination IP"),
                        _p("time_range", required=False, desc="Time range (e.g. last-24-hours)", example="last-24-hours"),
                    ],
                ),
                ProductAction(
                    id="get_threat_logs", name="Get Threat Logs",
                    description="Retrieve threat prevention logs (IPS, antivirus, anti-spyware).",
                    http_method="GET", endpoint_pattern="/v1/logs/threat",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("severity", required=False, desc="Minimum severity: critical/high/medium/low"),
                        _p("time_range", required=False, desc="Time range", example="last-1-hour"),
                    ],
                ),
            ],
        ),

        Product(
            id="fortinet_fortigate",
            name="Fortinet FortiGate",
            vendor="Fortinet",
            category=ProductCategory.FIREWALL,
            description="Enterprise firewall with SD-WAN, IPS, antivirus, web filtering, and application control.",
            auth_types=[AuthType.API_KEY, AuthType.BEARER],
            base_url_pattern="https://{fortigate_host}/api/v2",
            logo_abbr="FG",
            logo_color="bg-red-700",
            actions=[
                ProductAction(
                    id="block_ip", name="Block IP Address",
                    description="Add an IP to the firewall address blocklist and apply to deny policy.",
                    http_method="POST", endpoint_pattern="/cmdb/firewall/address",
                    cacao_activity=PlaybookActivityType.DENY_ACTIVITY,
                    parameters=[
                        _p("ip_address", "ipv4-addr", desc="IP address to block"),
                        _p("name", desc="Address object name"),
                    ],
                ),
                ProductAction(
                    id="quarantine_host", name="Quarantine Host",
                    description="Quarantine an endpoint by MAC address using FortiGate NAC.",
                    http_method="POST", endpoint_pattern="/monitor/user/banned/add_users",
                    cacao_activity=PlaybookActivityType.CONTAIN_SYSTEM,
                    parameters=[
                        _p("ip_address", "ipv4-addr", desc="IP of host to quarantine"),
                    ],
                ),
                ProductAction(
                    id="create_policy", name="Create Firewall Policy",
                    description="Create a new firewall policy rule.",
                    http_method="POST", endpoint_pattern="/cmdb/firewall/policy",
                    parameters=[
                        _p("name", desc="Policy name"),
                        _p("srcintf", desc="Source interface", example="port1"),
                        _p("dstintf", desc="Destination interface", example="port2"),
                        _p("action", desc="allow or deny", example="deny"),
                    ],
                ),
                ProductAction(
                    id="get_system_status", name="Get System Status",
                    description="Retrieve FortiGate system status and resource usage.",
                    http_method="GET", endpoint_pattern="/monitor/system/status",
                    parameters=[],
                ),
            ],
        ),

        Product(
            id="checkpoint_firewall",
            name="Check Point Firewall",
            vendor="Check Point",
            category=ProductCategory.FIREWALL,
            description="Enterprise security gateway with threat prevention, VPN, and centralized management.",
            auth_types=[AuthType.API_KEY, AuthType.BASIC],
            base_url_pattern="https://{mgmt_server}/web_api",
            logo_abbr="CP",
            logo_color="bg-purple-700",
            actions=[
                ProductAction(
                    id="add_to_blocklist", name="Add to Block List",
                    description="Add an IP, domain, or URL to the threat prevention block list.",
                    http_method="POST", endpoint_pattern="/v1.8/add-threat-indicator",
                    cacao_activity=PlaybookActivityType.DENY_ACTIVITY,
                    parameters=[
                        _p("indicator", desc="IP, domain, or URL to block"),
                        _p("indicator_type", desc="Type: IP/Domain/URL"),
                        _p("comment", required=False, desc="Reason for blocking"),
                    ],
                ),
                ProductAction(
                    id="create_access_rule", name="Create Access Rule",
                    description="Create a new access control rule in the security policy.",
                    http_method="POST", endpoint_pattern="/v1.8/add-access-rule",
                    parameters=[
                        _p("layer", desc="Policy layer name", example="Network"),
                        _p("name", desc="Rule name"),
                        _p("action", desc="Accept/Drop/Reject", example="Drop"),
                        _p("source", desc="Source object name"),
                        _p("destination", desc="Destination object name"),
                    ],
                ),
                ProductAction(
                    id="install_policy", name="Install Policy",
                    description="Push and install the security policy to gateway(s).",
                    http_method="POST", endpoint_pattern="/v1.8/install-policy",
                    parameters=[
                        _p("policy_package", desc="Policy package name", example="Standard"),
                        _p("targets", "list", desc="Gateway target names"),
                    ],
                ),
                ProductAction(
                    id="get_logs", name="Get Security Logs",
                    description="Query security event logs from SmartLog.",
                    http_method="POST", endpoint_pattern="/v1.8/show-logs",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("filter", required=False, desc="Log filter expression"),
                        _p("limit", "integer", required=False, desc="Max results", example="100"),
                    ],
                ),
            ],
        ),

        Product(
            id="cisco_asa",
            name="Cisco ASA / Firepower",
            vendor="Cisco",
            category=ProductCategory.FIREWALL,
            description="Adaptive Security Appliance with Firepower threat defense, IPS, and VPN.",
            auth_types=[AuthType.BASIC, AuthType.BEARER],
            base_url_pattern="https://{asa_host}/api",
            logo_abbr="CA",
            logo_color="bg-blue-700",
            actions=[
                ProductAction(
                    id="block_ip", name="Block IP via ACL",
                    description="Add a deny ACE to an access control list to block an IP.",
                    http_method="POST", endpoint_pattern="/access/in/InterfaceName/rules",
                    cacao_activity=PlaybookActivityType.DENY_ACTIVITY,
                    parameters=[
                        _p("source_ip", "ipv4-addr", desc="Source IP to block"),
                        _p("interface", desc="Interface name", example="outside"),
                        _p("permit", "boolean", desc="false for deny"),
                    ],
                ),
                ProductAction(
                    id="get_connections", name="Get Active Connections",
                    description="List active connections through the firewall.",
                    http_method="GET", endpoint_pattern="/monitoring/connections",
                    parameters=[
                        _p("source_ip", "ipv4-addr", required=False, desc="Filter by source"),
                    ],
                ),
                ProductAction(
                    id="get_threat_detection", name="Get Threat Detection Stats",
                    description="Retrieve threat detection scanning and rate statistics.",
                    http_method="GET", endpoint_pattern="/monitoring/threatdetection",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[],
                ),
            ],
        ),

        # ================================================================
        # EDR / XDR (5)
        # ================================================================
        Product(
            id="crowdstrike_falcon",
            name="CrowdStrike Falcon",
            vendor="CrowdStrike",
            category=ProductCategory.EDR_XDR,
            description="Cloud-native endpoint protection platform with EDR, threat intelligence, and real-time response.",
            auth_types=[AuthType.OAUTH2],
            base_url_pattern="https://api.crowdstrike.com",
            logo_abbr="CS",
            logo_color="bg-red-500",
            actions=[
                ProductAction(
                    id="isolate_host", name="Isolate Host",
                    description="Network-isolate a compromised endpoint (host still reports to CrowdStrike).",
                    http_method="POST", endpoint_pattern="/devices/entities/devices-actions/v2?action_name=contain",
                    cacao_activity=PlaybookActivityType.ISOLATE_SYSTEM,
                    parameters=[
                        _p("device_id", desc="CrowdStrike device/host ID"),
                    ],
                ),
                ProductAction(
                    id="lift_containment", name="Lift Containment",
                    description="Remove network isolation from an endpoint.",
                    http_method="POST", endpoint_pattern="/devices/entities/devices-actions/v2?action_name=lift_containment",
                    cacao_activity=PlaybookActivityType.RESTORE_SYSTEM,
                    parameters=[
                        _p("device_id", desc="CrowdStrike device/host ID"),
                    ],
                ),
                ProductAction(
                    id="get_detections", name="Get Detections",
                    description="Query recent detection events with filtering.",
                    http_method="GET", endpoint_pattern="/detects/queries/detects/v1",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("filter", required=False, desc="FQL filter", example="severity:>=4"),
                        _p("limit", "integer", required=False, desc="Max results", example="50"),
                    ],
                ),
                ProductAction(
                    id="get_device_info", name="Get Device Info",
                    description="Retrieve detailed information about a specific device.",
                    http_method="GET", endpoint_pattern="/devices/entities/devices/v2",
                    parameters=[
                        _p("device_id", desc="CrowdStrike device ID"),
                    ],
                ),
                ProductAction(
                    id="scan_host", name="Initiate On-Demand Scan",
                    description="Trigger an on-demand malware scan on an endpoint.",
                    http_method="POST", endpoint_pattern="/real-time-response/entities/command/v1",
                    cacao_activity=PlaybookActivityType.SCAN_SYSTEM,
                    parameters=[
                        _p("device_id", desc="Target device ID"),
                        _p("base_command", desc="RTR command", example="runscript"),
                    ],
                ),
            ],
        ),

        Product(
            id="sentinelone",
            name="SentinelOne Singularity",
            vendor="SentinelOne",
            category=ProductCategory.EDR_XDR,
            description="Autonomous endpoint protection with AI-driven detection, response, and remediation.",
            auth_types=[AuthType.API_KEY],
            base_url_pattern="https://{s1_host}/web/api/v2.1",
            logo_abbr="S1",
            logo_color="bg-purple-600",
            actions=[
                ProductAction(
                    id="isolate_endpoint", name="Disconnect from Network",
                    description="Isolate an endpoint from the network while maintaining agent connectivity.",
                    http_method="POST", endpoint_pattern="/agents/actions/disconnect",
                    cacao_activity=PlaybookActivityType.ISOLATE_SYSTEM,
                    parameters=[
                        _p("agent_id", desc="SentinelOne agent ID"),
                    ],
                ),
                ProductAction(
                    id="reconnect_endpoint", name="Reconnect to Network",
                    description="Restore network connectivity to a previously isolated endpoint.",
                    http_method="POST", endpoint_pattern="/agents/actions/connect",
                    cacao_activity=PlaybookActivityType.RESTORE_SYSTEM,
                    parameters=[
                        _p("agent_id", desc="SentinelOne agent ID"),
                    ],
                ),
                ProductAction(
                    id="get_threats", name="Get Threats",
                    description="Query active threats across endpoints.",
                    http_method="GET", endpoint_pattern="/threats",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("resolved", "boolean", required=False, desc="Filter resolved/unresolved"),
                        _p("limit", "integer", required=False, desc="Max results", example="100"),
                    ],
                ),
                ProductAction(
                    id="kill_process", name="Kill Process",
                    description="Terminate a running process on an endpoint.",
                    http_method="POST", endpoint_pattern="/agents/{agent_id}/actions/kill-process",
                    cacao_activity=PlaybookActivityType.CONTAIN_SYSTEM,
                    parameters=[
                        _p("agent_id", desc="Target agent ID"),
                        _p("process_name", desc="Process name to terminate"),
                    ],
                ),
                ProductAction(
                    id="initiate_scan", name="Initiate Full Scan",
                    description="Start a full disk scan on an endpoint.",
                    http_method="POST", endpoint_pattern="/agents/actions/initiate-scan",
                    cacao_activity=PlaybookActivityType.SCAN_SYSTEM,
                    parameters=[
                        _p("agent_id", desc="Target agent ID"),
                    ],
                ),
            ],
        ),

        Product(
            id="ms_defender_endpoint",
            name="Microsoft Defender for Endpoint",
            vendor="Microsoft",
            category=ProductCategory.EDR_XDR,
            description="Enterprise endpoint security with EDR, automated investigation, and advanced hunting.",
            auth_types=[AuthType.OAUTH2, AuthType.BEARER],
            base_url_pattern="https://api.securitycenter.microsoft.com/api",
            logo_abbr="MDE",
            logo_color="bg-blue-600",
            actions=[
                ProductAction(
                    id="isolate_machine", name="Isolate Machine",
                    description="Isolate a device from the network. Device keeps Defender connectivity.",
                    http_method="POST", endpoint_pattern="/machines/{machine_id}/isolate",
                    cacao_activity=PlaybookActivityType.ISOLATE_SYSTEM,
                    parameters=[
                        _p("machine_id", desc="Defender machine ID or device name"),
                        _p("isolation_type", desc="Full or Selective", example="Full"),
                        _p("comment", desc="Reason for isolation"),
                    ],
                ),
                ProductAction(
                    id="unisolate_machine", name="Release from Isolation",
                    description="Remove network isolation from a device.",
                    http_method="POST", endpoint_pattern="/machines/{machine_id}/unisolate",
                    cacao_activity=PlaybookActivityType.RESTORE_SYSTEM,
                    parameters=[
                        _p("machine_id", desc="Defender machine ID"),
                        _p("comment", desc="Reason for release"),
                    ],
                ),
                ProductAction(
                    id="run_av_scan", name="Run Antivirus Scan",
                    description="Initiate a quick or full antivirus scan on the device.",
                    http_method="POST", endpoint_pattern="/machines/{machine_id}/runAntiVirusScan",
                    cacao_activity=PlaybookActivityType.SCAN_SYSTEM,
                    parameters=[
                        _p("machine_id", desc="Defender machine ID"),
                        _p("scan_type", desc="Quick or Full", example="Full"),
                        _p("comment", desc="Scan reason"),
                    ],
                ),
                ProductAction(
                    id="get_alerts", name="Get Security Alerts",
                    description="List alerts filtered by severity, status, or time.",
                    http_method="GET", endpoint_pattern="/alerts",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("severity", required=False, desc="Filter: Informational/Low/Medium/High"),
                        _p("status", required=False, desc="Filter: New/InProgress/Resolved"),
                    ],
                ),
                ProductAction(
                    id="stop_and_quarantine_file", name="Stop & Quarantine File",
                    description="Stop execution of a file and quarantine it on the endpoint.",
                    http_method="POST", endpoint_pattern="/machines/{machine_id}/StopAndQuarantineFile",
                    cacao_activity=PlaybookActivityType.CONTAIN_SYSTEM,
                    parameters=[
                        _p("machine_id", desc="Defender machine ID"),
                        _p("sha1", "hash", desc="SHA1 hash of the file"),
                        _p("comment", desc="Reason"),
                    ],
                ),
            ],
        ),

        Product(
            id="vmware_carbon_black",
            name="VMware Carbon Black",
            vendor="VMware (Broadcom)",
            category=ProductCategory.EDR_XDR,
            description="Cloud-native endpoint protection with next-gen AV, EDR, and managed detection.",
            auth_types=[AuthType.API_KEY],
            base_url_pattern="https://{cb_host}/appservices/v6/orgs/{org_key}",
            logo_abbr="CB",
            logo_color="bg-gray-700",
            actions=[
                ProductAction(
                    id="isolate_device", name="Quarantine Device",
                    description="Quarantine (network-isolate) a device.",
                    http_method="POST", endpoint_pattern="/device_actions",
                    cacao_activity=PlaybookActivityType.ISOLATE_SYSTEM,
                    parameters=[
                        _p("device_id", "list", desc="Device ID(s) to quarantine"),
                        _p("action_type", desc="Action type", example="QUARANTINE"),
                    ],
                ),
                ProductAction(
                    id="ban_hash", name="Ban Hash",
                    description="Add a SHA-256 hash to the banned list (organization-wide block).",
                    http_method="POST", endpoint_pattern="/reputations/overrides",
                    cacao_activity=PlaybookActivityType.DENY_ACTIVITY,
                    parameters=[
                        _p("sha256_hash", "hash", desc="SHA-256 hash to ban"),
                        _p("description", desc="Reason for ban"),
                        _p("override_list", desc="BLACK_LIST", example="BLACK_LIST"),
                    ],
                ),
                ProductAction(
                    id="get_alerts", name="Get Alerts",
                    description="Search for alerts using query criteria.",
                    http_method="POST", endpoint_pattern="/alerts/_search",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("query", required=False, desc="Search query"),
                        _p("rows", "integer", required=False, desc="Max results", example="50"),
                    ],
                ),
                ProductAction(
                    id="search_processes", name="Search Processes",
                    description="Search process execution history across endpoints.",
                    http_method="POST", endpoint_pattern="/processes/_search",
                    cacao_activity=PlaybookActivityType.INVESTIGATE_SYSTEM,
                    parameters=[
                        _p("query", desc="Process search query", example="process_name:cmd.exe"),
                        _p("rows", "integer", required=False, desc="Max results"),
                    ],
                ),
            ],
        ),

        Product(
            id="cortex_xdr",
            name="Cortex XDR",
            vendor="Palo Alto Networks",
            category=ProductCategory.EDR_XDR,
            description="Extended detection and response platform unifying endpoint, network, and cloud data.",
            auth_types=[AuthType.API_KEY, AuthType.BEARER],
            base_url_pattern="https://api-{tenant}.xdr.{region}.paloaltonetworks.com/public_api/v1",
            logo_abbr="XDR",
            logo_color="bg-orange-600",
            actions=[
                ProductAction(
                    id="isolate_endpoint", name="Isolate Endpoint",
                    description="Isolate one or more endpoints from the network.",
                    http_method="POST", endpoint_pattern="/endpoints/isolate",
                    cacao_activity=PlaybookActivityType.ISOLATE_SYSTEM,
                    parameters=[
                        _p("endpoint_id", desc="Cortex XDR endpoint ID"),
                    ],
                ),
                ProductAction(
                    id="unisolate_endpoint", name="Unisolate Endpoint",
                    description="Remove network isolation from endpoints.",
                    http_method="POST", endpoint_pattern="/endpoints/unisolate",
                    cacao_activity=PlaybookActivityType.RESTORE_SYSTEM,
                    parameters=[
                        _p("endpoint_id", desc="Cortex XDR endpoint ID"),
                    ],
                ),
                ProductAction(
                    id="get_incidents", name="Get Incidents",
                    description="Retrieve a list of incidents with optional filtering.",
                    http_method="POST", endpoint_pattern="/incidents/get_incidents",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("limit", "integer", required=False, desc="Max results", example="100"),
                        _p("sort_field", required=False, desc="Sort by field", example="creation_time"),
                    ],
                ),
                ProductAction(
                    id="get_alerts", name="Get Alerts",
                    description="Get detailed alert information.",
                    http_method="POST", endpoint_pattern="/alerts/get_alerts_multi_events",
                    parameters=[
                        _p("alert_id", required=False, desc="Specific alert ID"),
                        _p("severity", required=False, desc="Filter by severity"),
                    ],
                ),
                ProductAction(
                    id="scan_endpoint", name="Scan Endpoint",
                    description="Initiate a malware scan on specified endpoints.",
                    http_method="POST", endpoint_pattern="/endpoints/scan",
                    cacao_activity=PlaybookActivityType.SCAN_SYSTEM,
                    parameters=[
                        _p("endpoint_id", desc="Target endpoint ID"),
                    ],
                ),
                ProductAction(
                    id="block_file_hash", name="Block File by Hash",
                    description="Add a file hash to the block list to prevent execution.",
                    http_method="POST", endpoint_pattern="/hash_exceptions/blocklist",
                    cacao_activity=PlaybookActivityType.DENY_ACTIVITY,
                    parameters=[
                        _p("hash_value", "hash", desc="SHA-256 file hash"),
                        _p("comment", required=False, desc="Reason for blocking"),
                    ],
                ),
            ],
        ),

        # ================================================================
        # SIEM (3)
        # ================================================================
        Product(
            id="splunk_enterprise",
            name="Splunk Enterprise / Cloud",
            vendor="Splunk (Cisco)",
            category=ProductCategory.SIEM,
            description="Security information and event management with advanced search, alerting, and dashboards.",
            auth_types=[AuthType.BEARER, AuthType.BASIC],
            base_url_pattern="https://{splunk_host}:8089/services",
            logo_abbr="SPL",
            logo_color="bg-green-600",
            actions=[
                ProductAction(
                    id="search", name="Run Search Query",
                    description="Execute a Splunk search (SPL) query and return results.",
                    http_method="POST", endpoint_pattern="/search/jobs",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("search_query", desc="SPL search query", example="index=main sourcetype=syslog"),
                        _p("earliest_time", required=False, desc="Start time", example="-24h"),
                        _p("latest_time", required=False, desc="End time", example="now"),
                    ],
                ),
                ProductAction(
                    id="create_notable", name="Create Notable Event",
                    description="Create a notable event in Splunk Enterprise Security.",
                    http_method="POST", endpoint_pattern="/notable_update",
                    cacao_activity=PlaybookActivityType.COMPOSE_CONTENT,
                    parameters=[
                        _p("rule_title", desc="Notable event title"),
                        _p("urgency", desc="Urgency: critical/high/medium/low/informational"),
                        _p("security_domain", desc="Domain: access/endpoint/network/threat"),
                    ],
                ),
                ProductAction(
                    id="get_alerts", name="Get Triggered Alerts",
                    description="List fired/triggered alert actions.",
                    http_method="GET", endpoint_pattern="/alerts/fired_alerts",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("count", "integer", required=False, desc="Max results", example="50"),
                    ],
                ),
            ],
        ),

        Product(
            id="ibm_qradar",
            name="IBM QRadar",
            vendor="IBM",
            category=ProductCategory.SIEM,
            description="Security intelligence platform for log management, threat detection, and incident forensics.",
            auth_types=[AuthType.API_KEY],
            base_url_pattern="https://{qradar_host}/api",
            logo_abbr="QR",
            logo_color="bg-blue-800",
            actions=[
                ProductAction(
                    id="search_ariel", name="Run AQL Search",
                    description="Execute an Ariel Query Language (AQL) search against QRadar.",
                    http_method="POST", endpoint_pattern="/ariel/searches",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("query_expression", desc="AQL query", example="SELECT * FROM events WHERE severity > 5 LAST 1 HOURS"),
                    ],
                ),
                ProductAction(
                    id="get_offenses", name="Get Offenses",
                    description="Retrieve security offenses (incidents) from QRadar.",
                    http_method="GET", endpoint_pattern="/siem/offenses",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("filter", required=False, desc="API filter", example="status=OPEN"),
                        _p("range", required=False, desc="Range header", example="items=0-49"),
                    ],
                ),
                ProductAction(
                    id="close_offense", name="Close Offense",
                    description="Close a QRadar offense with a closing reason.",
                    http_method="POST", endpoint_pattern="/siem/offenses/{offense_id}",
                    parameters=[
                        _p("offense_id", "integer", desc="Offense ID"),
                        _p("closing_reason_id", "integer", desc="Closing reason ID"),
                        _p("status", desc="CLOSED", example="CLOSED"),
                    ],
                ),
                ProductAction(
                    id="add_to_reference_set", name="Add to Reference Set",
                    description="Add an indicator to a QRadar reference set (e.g., blocklist).",
                    http_method="POST", endpoint_pattern="/reference_data/sets/{name}",
                    cacao_activity=PlaybookActivityType.DEPLOY_COUNTERMEASURE,
                    parameters=[
                        _p("name", desc="Reference set name", example="Blocked_IPs"),
                        _p("value", desc="Value to add", example="10.0.0.1"),
                    ],
                ),
            ],
        ),

        Product(
            id="elastic_siem",
            name="Elastic Security (SIEM)",
            vendor="Elastic",
            category=ProductCategory.SIEM,
            description="Open security analytics with SIEM, endpoint security, and cloud security in the Elastic Stack.",
            auth_types=[AuthType.API_KEY, AuthType.BASIC],
            base_url_pattern="https://{elastic_host}:9200",
            logo_abbr="ELK",
            logo_color="bg-yellow-500",
            actions=[
                ProductAction(
                    id="search", name="Elasticsearch Search",
                    description="Execute an Elasticsearch query across security indices.",
                    http_method="POST", endpoint_pattern="/{index}/_search",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("index", desc="Index pattern", example=".siem-signals-*"),
                        _p("query", desc="Elasticsearch query DSL (JSON)"),
                        _p("size", "integer", required=False, desc="Max results", example="100"),
                    ],
                ),
                ProductAction(
                    id="get_alerts", name="Get Detection Alerts",
                    description="Retrieve Elastic Security detection alerts.",
                    http_method="POST", endpoint_pattern="/api/detection_engine/signals/search",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("query", required=False, desc="KQL filter query"),
                        _p("size", "integer", required=False, desc="Max results"),
                    ],
                ),
                ProductAction(
                    id="create_rule", name="Create Detection Rule",
                    description="Create a new detection rule in Elastic Security.",
                    http_method="POST", endpoint_pattern="/api/detection_engine/rules",
                    cacao_activity=PlaybookActivityType.DEPLOY_COUNTERMEASURE,
                    parameters=[
                        _p("name", desc="Rule name"),
                        _p("rule_type", desc="query/eql/threshold/machine_learning"),
                        _p("query", desc="Detection query"),
                        _p("severity", desc="low/medium/high/critical"),
                    ],
                ),
            ],
        ),

        # ================================================================
        # EMAIL SECURITY (3)
        # ================================================================
        Product(
            id="proofpoint_tap",
            name="Proofpoint TAP",
            vendor="Proofpoint",
            category=ProductCategory.EMAIL_SECURITY,
            description="Targeted Attack Protection for advanced email threats, phishing, and business email compromise.",
            auth_types=[AuthType.BASIC],
            base_url_pattern="https://tap-api-v2.proofpoint.com/v2",
            logo_abbr="PP",
            logo_color="bg-teal-600",
            actions=[
                ProductAction(
                    id="get_blocked_messages", name="Get Blocked Messages",
                    description="Retrieve messages blocked by Proofpoint in a time period.",
                    http_method="GET", endpoint_pattern="/siem/messages/blocked",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("sinceSeconds", "integer", desc="Time window in seconds", example="3600"),
                    ],
                ),
                ProductAction(
                    id="get_delivered_threats", name="Get Delivered Threats",
                    description="Retrieve messages that were delivered but contained threats.",
                    http_method="GET", endpoint_pattern="/siem/messages/delivered",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("sinceSeconds", "integer", desc="Time window in seconds", example="3600"),
                    ],
                ),
                ProductAction(
                    id="get_clicks_blocked", name="Get Blocked Clicks",
                    description="Retrieve URL clicks that were blocked by Proofpoint.",
                    http_method="GET", endpoint_pattern="/siem/clicks/blocked",
                    parameters=[
                        _p("sinceSeconds", "integer", desc="Time window in seconds"),
                    ],
                ),
                ProductAction(
                    id="decode_url", name="Decode Proofpoint URL",
                    description="Decode a Proofpoint rewritten/encoded URL to its original form.",
                    http_method="POST", endpoint_pattern="/url/decode",
                    parameters=[
                        _p("urls", "list", desc="List of encoded URLs to decode"),
                    ],
                ),
            ],
        ),

        Product(
            id="mimecast",
            name="Mimecast",
            vendor="Mimecast",
            category=ProductCategory.EMAIL_SECURITY,
            description="Cloud email security with anti-spam, anti-malware, DLP, and archiving.",
            auth_types=[AuthType.OAUTH2, AuthType.API_KEY],
            base_url_pattern="https://{region}-api.mimecast.com/api",
            logo_abbr="MC",
            logo_color="bg-blue-500",
            actions=[
                ProductAction(
                    id="block_sender", name="Block Sender",
                    description="Add a sender email/domain to the block list.",
                    http_method="POST", endpoint_pattern="/managedsender/permit-or-block-sender",
                    cacao_activity=PlaybookActivityType.DENY_ACTIVITY,
                    parameters=[
                        _p("sender", desc="Email address or domain to block"),
                        _p("to", desc="Recipient policy applies to"),
                        _p("action", desc="block", example="block"),
                    ],
                ),
                ProductAction(
                    id="get_held_messages", name="Get Held Messages",
                    description="Retrieve messages held in the Mimecast hold queue.",
                    http_method="POST", endpoint_pattern="/gateway/get-hold-message-list",
                    parameters=[
                        _p("admin", "boolean", required=False, desc="Admin mode"),
                    ],
                ),
                ProductAction(
                    id="search_message_tracking", name="Search Message Tracking",
                    description="Search email message tracking logs.",
                    http_method="POST", endpoint_pattern="/message-finder/search-message-tracking",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("search_reason", desc="Reason for search"),
                        _p("sender", required=False, desc="Sender email filter"),
                        _p("recipient", required=False, desc="Recipient email filter"),
                        _p("start", required=False, desc="Start datetime"),
                        _p("end", required=False, desc="End datetime"),
                    ],
                ),
            ],
        ),

        Product(
            id="ms_defender_office365",
            name="Microsoft Defender for Office 365",
            vendor="Microsoft",
            category=ProductCategory.EMAIL_SECURITY,
            description="Email and collaboration security with anti-phishing, safe links, safe attachments, and automated investigation.",
            auth_types=[AuthType.OAUTH2, AuthType.BEARER],
            base_url_pattern="https://graph.microsoft.com/v1.0/security",
            logo_abbr="MDO",
            logo_color="bg-blue-600",
            actions=[
                ProductAction(
                    id="get_quarantined_messages", name="Get Quarantined Messages",
                    description="List messages quarantined by Exchange Online Protection.",
                    http_method="GET", endpoint_pattern="/threatSubmission/emailThreats",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("filter", required=False, desc="OData filter expression"),
                    ],
                ),
                ProductAction(
                    id="release_quarantine", name="Release from Quarantine",
                    description="Release a quarantined message to the recipient.",
                    http_method="POST", endpoint_pattern="/threatSubmission/emailThreats/{id}/release",
                    parameters=[
                        _p("message_id", desc="Quarantined message ID"),
                    ],
                ),
                ProductAction(
                    id="submit_threat", name="Submit Threat for Analysis",
                    description="Submit a suspicious email, URL, or file for Microsoft threat analysis.",
                    http_method="POST", endpoint_pattern="/threatSubmission/emailThreats",
                    parameters=[
                        _p("category", desc="spam/phish/malware"),
                        _p("content_type", desc="Type of content submitted"),
                        _p("message_url", required=False, desc="URL of message"),
                    ],
                ),
            ],
        ),

        # ================================================================
        # WAF (2)
        # ================================================================
        Product(
            id="cloudflare_waf",
            name="Cloudflare WAF",
            vendor="Cloudflare",
            category=ProductCategory.WAF,
            description="Web Application Firewall with DDoS protection, bot management, and rate limiting.",
            auth_types=[AuthType.API_KEY, AuthType.BEARER],
            base_url_pattern="https://api.cloudflare.com/client/v4",
            logo_abbr="CF",
            logo_color="bg-orange-500",
            actions=[
                ProductAction(
                    id="block_ip", name="Block IP via Firewall Rule",
                    description="Create a firewall rule to block a specific IP address.",
                    http_method="POST", endpoint_pattern="/zones/{zone_id}/firewall/access_rules/rules",
                    cacao_activity=PlaybookActivityType.DENY_ACTIVITY,
                    parameters=[
                        _p("ip_address", "ipv4-addr", desc="IP to block"),
                        _p("mode", desc="block/challenge/js_challenge", example="block"),
                        _p("notes", required=False, desc="Rule notes"),
                    ],
                ),
                ProductAction(
                    id="create_waf_rule", name="Create Custom WAF Rule",
                    description="Create a custom WAF rule using Cloudflare's ruleset engine.",
                    http_method="POST", endpoint_pattern="/zones/{zone_id}/rulesets/{ruleset_id}/rules",
                    cacao_activity=PlaybookActivityType.DEPLOY_COUNTERMEASURE,
                    parameters=[
                        _p("expression", desc="Wirefilter expression"),
                        _p("action", desc="block/managed_challenge/log"),
                        _p("description", required=False, desc="Rule description"),
                    ],
                ),
                ProductAction(
                    id="get_analytics", name="Get Security Analytics",
                    description="Retrieve WAF analytics and attack statistics.",
                    http_method="GET", endpoint_pattern="/zones/{zone_id}/analytics/dashboard",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("since", required=False, desc="Start time (ISO 8601)"),
                        _p("until", required=False, desc="End time (ISO 8601)"),
                    ],
                ),
            ],
        ),

        Product(
            id="aws_waf",
            name="AWS WAF",
            vendor="Amazon Web Services",
            category=ProductCategory.WAF,
            description="Cloud web application firewall for protecting AWS resources from common web exploits.",
            auth_types=[AuthType.API_KEY],
            base_url_pattern="https://wafv2.{region}.amazonaws.com",
            logo_abbr="AWS",
            logo_color="bg-yellow-600",
            actions=[
                ProductAction(
                    id="create_ip_set", name="Create IP Set",
                    description="Create an IP set for use in WAF rules (blocklist/allowlist).",
                    http_method="POST", endpoint_pattern="/",
                    cacao_activity=PlaybookActivityType.DEPLOY_COUNTERMEASURE,
                    parameters=[
                        _p("name", desc="IP set name"),
                        _p("addresses", "list", desc="List of IP/CIDR addresses"),
                        _p("ip_address_version", desc="IPV4 or IPV6", example="IPV4"),
                        _p("scope", desc="REGIONAL or CLOUDFRONT", example="REGIONAL"),
                    ],
                ),
                ProductAction(
                    id="update_ip_set", name="Update IP Set",
                    description="Add or remove addresses from an existing IP set.",
                    http_method="POST", endpoint_pattern="/",
                    parameters=[
                        _p("ip_set_id", desc="IP set ID"),
                        _p("addresses", "list", desc="Updated list of IP/CIDR addresses"),
                        _p("lock_token", desc="Lock token for concurrency"),
                    ],
                ),
                ProductAction(
                    id="get_sampled_requests", name="Get Sampled Requests",
                    description="Retrieve a sample of recent web requests matched by WAF rules.",
                    http_method="POST", endpoint_pattern="/",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("web_acl_arn", desc="Web ACL ARN"),
                        _p("rule_metric_name", desc="Rule metric name"),
                        _p("max_items", "integer", required=False, desc="Max samples", example="100"),
                    ],
                ),
            ],
        ),

        # ================================================================
        # IDENTITY / IAM (4)
        # ================================================================
        Product(
            id="entra_id",
            name="Microsoft Entra ID",
            vendor="Microsoft",
            category=ProductCategory.IDENTITY_IAM,
            description="Cloud identity and access management (formerly Azure AD) with conditional access, MFA, and identity protection.",
            auth_types=[AuthType.OAUTH2, AuthType.BEARER],
            base_url_pattern="https://graph.microsoft.com/v1.0",
            logo_abbr="EID",
            logo_color="bg-blue-500",
            actions=[
                ProductAction(
                    id="disable_user", name="Disable User Account",
                    description="Disable a user account to prevent sign-in.",
                    http_method="PATCH", endpoint_pattern="/users/{user_id}",
                    cacao_activity=PlaybookActivityType.CONTAIN_SYSTEM,
                    parameters=[
                        _p("user_id", desc="User ID or UPN", example="user@company.com"),
                        _p("accountEnabled", "boolean", desc="Set to false", example="false"),
                    ],
                ),
                ProductAction(
                    id="enable_user", name="Enable User Account",
                    description="Re-enable a disabled user account.",
                    http_method="PATCH", endpoint_pattern="/users/{user_id}",
                    cacao_activity=PlaybookActivityType.RESTORE_SYSTEM,
                    parameters=[
                        _p("user_id", desc="User ID or UPN"),
                        _p("accountEnabled", "boolean", desc="Set to true", example="true"),
                    ],
                ),
                ProductAction(
                    id="revoke_sessions", name="Revoke Sign-In Sessions",
                    description="Invalidate all refresh tokens and session cookies for a user.",
                    http_method="POST", endpoint_pattern="/users/{user_id}/revokeSignInSessions",
                    cacao_activity=PlaybookActivityType.CONTAIN_SYSTEM,
                    parameters=[
                        _p("user_id", desc="User ID or UPN"),
                    ],
                ),
                ProductAction(
                    id="get_sign_in_logs", name="Get Sign-In Logs",
                    description="Retrieve sign-in activity logs for a user or organization.",
                    http_method="GET", endpoint_pattern="/auditLogs/signIns",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("filter", required=False, desc="OData filter", example="userPrincipalName eq 'user@company.com'"),
                        _p("top", "integer", required=False, desc="Max results", example="50"),
                    ],
                ),
                ProductAction(
                    id="get_risky_users", name="Get Risky Users",
                    description="List users flagged as risky by Identity Protection.",
                    http_method="GET", endpoint_pattern="/identityProtection/riskyUsers",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("riskLevel", required=False, desc="low/medium/high"),
                    ],
                ),
                ProductAction(
                    id="reset_password", name="Reset User Password",
                    description="Force a password reset for a user account.",
                    http_method="POST", endpoint_pattern="/users/{user_id}/authentication/methods/{method_id}/resetPassword",
                    cacao_activity=PlaybookActivityType.MITIGATE_VULNERABILITY,
                    parameters=[
                        _p("user_id", desc="User ID or UPN"),
                        _p("new_password", required=False, desc="New password (auto-generated if empty)"),
                    ],
                ),
            ],
        ),

        Product(
            id="active_directory",
            name="Active Directory (On-Prem)",
            vendor="Microsoft",
            category=ProductCategory.IDENTITY_IAM,
            description="On-premises directory service for Windows domain networks with authentication, group policy, and LDAP.",
            auth_types=[AuthType.BASIC, AuthType.CERTIFICATE],
            base_url_pattern="ldaps://{dc_host}:636",
            logo_abbr="AD",
            logo_color="bg-blue-700",
            actions=[
                ProductAction(
                    id="disable_account", name="Disable AD Account",
                    description="Disable a user account in Active Directory.",
                    http_method="POST", endpoint_pattern="/ad/users/{samAccountName}/disable",
                    cacao_activity=PlaybookActivityType.CONTAIN_SYSTEM,
                    parameters=[
                        _p("samAccountName", desc="AD username (sAMAccountName)"),
                    ],
                ),
                ProductAction(
                    id="reset_password", name="Reset AD Password",
                    description="Reset a user's Active Directory password.",
                    http_method="POST", endpoint_pattern="/ad/users/{samAccountName}/resetPassword",
                    cacao_activity=PlaybookActivityType.MITIGATE_VULNERABILITY,
                    parameters=[
                        _p("samAccountName", desc="AD username"),
                        _p("new_password", desc="New password"),
                        _p("must_change", "boolean", required=False, desc="Force change at next logon", example="true"),
                    ],
                ),
                ProductAction(
                    id="get_user_groups", name="Get User Groups",
                    description="List all groups a user is a member of.",
                    http_method="GET", endpoint_pattern="/ad/users/{samAccountName}/groups",
                    cacao_activity=PlaybookActivityType.INVESTIGATE_SYSTEM,
                    parameters=[
                        _p("samAccountName", desc="AD username"),
                    ],
                ),
                ProductAction(
                    id="lock_account", name="Lock AD Account",
                    description="Lock a user account to prevent authentication.",
                    http_method="POST", endpoint_pattern="/ad/users/{samAccountName}/lock",
                    cacao_activity=PlaybookActivityType.CONTAIN_SYSTEM,
                    parameters=[
                        _p("samAccountName", desc="AD username"),
                    ],
                ),
            ],
        ),

        Product(
            id="okta",
            name="Okta",
            vendor="Okta",
            category=ProductCategory.IDENTITY_IAM,
            description="Cloud identity provider with SSO, MFA, lifecycle management, and universal directory.",
            auth_types=[AuthType.API_KEY, AuthType.OAUTH2],
            base_url_pattern="https://{okta_domain}/api/v1",
            logo_abbr="OK",
            logo_color="bg-indigo-600",
            actions=[
                ProductAction(
                    id="suspend_user", name="Suspend User",
                    description="Suspend a user account (reversible deactivation).",
                    http_method="POST", endpoint_pattern="/users/{user_id}/lifecycle/suspend",
                    cacao_activity=PlaybookActivityType.CONTAIN_SYSTEM,
                    parameters=[
                        _p("user_id", desc="Okta user ID or login email"),
                    ],
                ),
                ProductAction(
                    id="unsuspend_user", name="Unsuspend User",
                    description="Reactivate a suspended user account.",
                    http_method="POST", endpoint_pattern="/users/{user_id}/lifecycle/unsuspend",
                    cacao_activity=PlaybookActivityType.RESTORE_SYSTEM,
                    parameters=[
                        _p("user_id", desc="Okta user ID"),
                    ],
                ),
                ProductAction(
                    id="clear_sessions", name="Clear User Sessions",
                    description="Terminate all active sessions for a user.",
                    http_method="DELETE", endpoint_pattern="/users/{user_id}/sessions",
                    cacao_activity=PlaybookActivityType.CONTAIN_SYSTEM,
                    parameters=[
                        _p("user_id", desc="Okta user ID"),
                    ],
                ),
                ProductAction(
                    id="get_system_log", name="Get System Log",
                    description="Query the Okta system log for events.",
                    http_method="GET", endpoint_pattern="/logs",
                    cacao_activity=PlaybookActivityType.ANALYZE_COLLECTED_DATA,
                    parameters=[
                        _p("filter", required=False, desc="SCIM filter expression"),
                        _p("since", required=False, desc="Start datetime (ISO 8601)"),
                        _p("limit", "integer", required=False, desc="Max results", example="100"),
                    ],
                ),
            ],
        ),

        Product(
            id="cyberark",
            name="CyberArk Privileged Access",
            vendor="CyberArk",
            category=ProductCategory.IDENTITY_IAM,
            description="Privileged access management for securing, managing, and monitoring privileged accounts and credentials.",
            auth_types=[AuthType.BASIC, AuthType.OAUTH2],
            base_url_pattern="https://{cyberark_host}/PasswordVault/api",
            logo_abbr="CA",
            logo_color="bg-blue-900",
            actions=[
                ProductAction(
                    id="get_accounts", name="Get Privileged Accounts",
                    description="List privileged accounts in the vault.",
                    http_method="GET", endpoint_pattern="/Accounts",
                    cacao_activity=PlaybookActivityType.INVESTIGATE_SYSTEM,
                    parameters=[
                        _p("search", required=False, desc="Search keyword"),
                        _p("filter", required=False, desc="Filter expression"),
                    ],
                ),
                ProductAction(
                    id="change_credential", name="Change Credential",
                    description="Initiate an immediate password change for a privileged account.",
                    http_method="POST", endpoint_pattern="/Accounts/{account_id}/Change",
                    cacao_activity=PlaybookActivityType.MITIGATE_VULNERABILITY,
                    parameters=[
                        _p("account_id", desc="CyberArk account ID"),
                        _p("change_entire_group", "boolean", required=False, desc="Change all linked accounts"),
                    ],
                ),
                ProductAction(
                    id="reconcile_account", name="Reconcile Account",
                    description="Reconcile a privileged account password with the target system.",
                    http_method="POST", endpoint_pattern="/Accounts/{account_id}/Reconcile",
                    parameters=[
                        _p("account_id", desc="CyberArk account ID"),
                    ],
                ),
            ],
        ),

        # ================================================================
        # THREAT INTELLIGENCE (3)
        # ================================================================
        Product(
            id="virustotal",
            name="VirusTotal",
            vendor="Google (Chronicle)",
            category=ProductCategory.THREAT_INTEL,
            description="Multi-engine malware scanning and threat intelligence service for files, URLs, IPs, and domains.",
            auth_types=[AuthType.API_KEY],
            base_url_pattern="https://www.virustotal.com/api/v3",
            logo_abbr="VT",
            logo_color="bg-blue-500",
            actions=[
                ProductAction(
                    id="lookup_hash", name="Lookup File Hash",
                    description="Get analysis report for a file hash (MD5/SHA1/SHA256).",
                    http_method="GET", endpoint_pattern="/files/{hash}",
                    cacao_activity=PlaybookActivityType.MATCH_INDICATORS,
                    parameters=[
                        _p("hash", "hash", desc="File hash (MD5/SHA1/SHA256)"),
                    ],
                ),
                ProductAction(
                    id="lookup_ip", name="Lookup IP Address",
                    description="Get reputation and analysis data for an IP address.",
                    http_method="GET", endpoint_pattern="/ip_addresses/{ip}",
                    cacao_activity=PlaybookActivityType.MATCH_INDICATORS,
                    parameters=[
                        _p("ip", "ipv4-addr", desc="IP address to check"),
                    ],
                ),
                ProductAction(
                    id="lookup_domain", name="Lookup Domain",
                    description="Get reputation and analysis data for a domain name.",
                    http_method="GET", endpoint_pattern="/domains/{domain}",
                    cacao_activity=PlaybookActivityType.MATCH_INDICATORS,
                    parameters=[
                        _p("domain", desc="Domain to check", example="example.com"),
                    ],
                ),
                ProductAction(
                    id="lookup_url", name="Lookup URL",
                    description="Get analysis results for a URL.",
                    http_method="POST", endpoint_pattern="/urls",
                    cacao_activity=PlaybookActivityType.MATCH_INDICATORS,
                    parameters=[
                        _p("url", "url", desc="URL to analyze"),
                    ],
                ),
                ProductAction(
                    id="submit_file", name="Submit File for Scanning",
                    description="Upload a file for multi-engine scanning.",
                    http_method="POST", endpoint_pattern="/files",
                    cacao_activity=PlaybookActivityType.SCAN_SYSTEM,
                    parameters=[
                        _p("file", desc="File path or binary content"),
                    ],
                ),
            ],
        ),

        Product(
            id="abuseipdb",
            name="AbuseIPDB",
            vendor="AbuseIPDB",
            category=ProductCategory.THREAT_INTEL,
            description="IP address abuse and threat reporting database for checking and reporting malicious IPs.",
            auth_types=[AuthType.API_KEY],
            base_url_pattern="https://api.abuseipdb.com/api/v2",
            logo_abbr="ADB",
            logo_color="bg-red-600",
            actions=[
                ProductAction(
                    id="check_ip", name="Check IP Reputation",
                    description="Check an IP address against the AbuseIPDB database.",
                    http_method="GET", endpoint_pattern="/check",
                    cacao_activity=PlaybookActivityType.MATCH_INDICATORS,
                    parameters=[
                        _p("ipAddress", "ipv4-addr", desc="IP to check"),
                        _p("maxAgeInDays", "integer", required=False, desc="Max report age", example="90"),
                    ],
                ),
                ProductAction(
                    id="report_ip", name="Report Malicious IP",
                    description="Report an IP address for abusive behavior.",
                    http_method="POST", endpoint_pattern="/report",
                    parameters=[
                        _p("ip", "ipv4-addr", desc="IP to report"),
                        _p("categories", "list", desc="Abuse category IDs"),
                        _p("comment", desc="Description of abuse"),
                    ],
                ),
                ProductAction(
                    id="get_blacklist", name="Get Blacklist",
                    description="Download the current AbuseIPDB blacklist.",
                    http_method="GET", endpoint_pattern="/blacklist",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("confidenceMinimum", "integer", required=False, desc="Min confidence score", example="75"),
                        _p("limit", "integer", required=False, desc="Max results", example="1000"),
                    ],
                ),
            ],
        ),

        Product(
            id="alienvault_otx",
            name="AlienVault OTX",
            vendor="AT&T Cybersecurity",
            category=ProductCategory.THREAT_INTEL,
            description="Open Threat Exchange community-driven threat intelligence platform with IOC sharing.",
            auth_types=[AuthType.API_KEY],
            base_url_pattern="https://otx.alienvault.com/api/v1",
            logo_abbr="OTX",
            logo_color="bg-green-700",
            actions=[
                ProductAction(
                    id="get_indicator", name="Get Indicator Details",
                    description="Retrieve comprehensive details for an IOC (IP, domain, hash, URL).",
                    http_method="GET", endpoint_pattern="/indicators/{type}/{indicator}/general",
                    cacao_activity=PlaybookActivityType.MATCH_INDICATORS,
                    parameters=[
                        _p("type", desc="Indicator type: IPv4/IPv6/domain/hostname/url/file"),
                        _p("indicator", desc="The IOC value"),
                    ],
                ),
                ProductAction(
                    id="get_pulse", name="Get Pulse Details",
                    description="Retrieve a specific OTX pulse (threat report) with IOCs.",
                    http_method="GET", endpoint_pattern="/pulses/{pulse_id}",
                    cacao_activity=PlaybookActivityType.IDENTIFY_INDICATORS,
                    parameters=[
                        _p("pulse_id", desc="OTX Pulse ID"),
                    ],
                ),
                ProductAction(
                    id="search_pulses", name="Search Pulses",
                    description="Search for pulses by keyword, tag, or adversary.",
                    http_method="GET", endpoint_pattern="/search/pulses",
                    parameters=[
                        _p("q", desc="Search query", example="ransomware"),
                        _p("limit", "integer", required=False, desc="Max results", example="20"),
                    ],
                ),
            ],
        ),

        # ================================================================
        # TICKETING (2)
        # ================================================================
        Product(
            id="servicenow",
            name="ServiceNow",
            vendor="ServiceNow",
            category=ProductCategory.TICKETING,
            description="Enterprise IT service management with incident management, change management, and workflow automation.",
            auth_types=[AuthType.BASIC, AuthType.OAUTH2],
            base_url_pattern="https://{instance}.service-now.com/api/now",
            logo_abbr="SN",
            logo_color="bg-green-500",
            actions=[
                ProductAction(
                    id="create_incident", name="Create Incident",
                    description="Create a new incident ticket in ServiceNow.",
                    http_method="POST", endpoint_pattern="/table/incident",
                    cacao_activity=PlaybookActivityType.COMPOSE_CONTENT,
                    parameters=[
                        _p("short_description", desc="Incident title"),
                        _p("description", desc="Detailed description"),
                        _p("urgency", desc="1-High/2-Medium/3-Low", example="2"),
                        _p("impact", desc="1-High/2-Medium/3-Low", example="2"),
                        _p("assignment_group", required=False, desc="Assignment group name"),
                    ],
                ),
                ProductAction(
                    id="update_incident", name="Update Incident",
                    description="Update fields on an existing incident ticket.",
                    http_method="PATCH", endpoint_pattern="/table/incident/{sys_id}",
                    parameters=[
                        _p("sys_id", desc="Incident sys_id"),
                        _p("work_notes", required=False, desc="Work notes to add"),
                        _p("state", required=False, desc="New state (1-8)", example="2"),
                    ],
                ),
                ProductAction(
                    id="close_incident", name="Close Incident",
                    description="Resolve and close an incident ticket.",
                    http_method="PATCH", endpoint_pattern="/table/incident/{sys_id}",
                    parameters=[
                        _p("sys_id", desc="Incident sys_id"),
                        _p("close_code", desc="Resolution code", example="Solved (Permanently)"),
                        _p("close_notes", desc="Resolution notes"),
                    ],
                ),
                ProductAction(
                    id="add_comment", name="Add Comment",
                    description="Add a comment or work note to an incident.",
                    http_method="PATCH", endpoint_pattern="/table/incident/{sys_id}",
                    parameters=[
                        _p("sys_id", desc="Incident sys_id"),
                        _p("comments", desc="Comment text"),
                    ],
                ),
            ],
        ),

        Product(
            id="jira",
            name="Jira",
            vendor="Atlassian",
            category=ProductCategory.TICKETING,
            description="Project and issue tracking for security incident management and vulnerability remediation workflows.",
            auth_types=[AuthType.API_KEY, AuthType.BASIC, AuthType.OAUTH2],
            base_url_pattern="https://{jira_host}/rest/api/3",
            logo_abbr="JR",
            logo_color="bg-blue-600",
            actions=[
                ProductAction(
                    id="create_issue", name="Create Issue",
                    description="Create a new Jira issue (task, bug, incident, etc.).",
                    http_method="POST", endpoint_pattern="/issue",
                    cacao_activity=PlaybookActivityType.COMPOSE_CONTENT,
                    parameters=[
                        _p("project_key", desc="Project key", example="SEC"),
                        _p("summary", desc="Issue title"),
                        _p("issue_type", desc="Bug/Task/Story/Incident", example="Task"),
                        _p("description", required=False, desc="Detailed description"),
                        _p("priority", required=False, desc="Highest/High/Medium/Low/Lowest"),
                    ],
                ),
                ProductAction(
                    id="update_issue", name="Update Issue",
                    description="Update fields on an existing Jira issue.",
                    http_method="PUT", endpoint_pattern="/issue/{issue_id_or_key}",
                    parameters=[
                        _p("issue_id_or_key", desc="Issue key", example="SEC-123"),
                        _p("summary", required=False, desc="New summary"),
                        _p("description", required=False, desc="New description"),
                    ],
                ),
                ProductAction(
                    id="add_comment", name="Add Comment",
                    description="Add a comment to a Jira issue.",
                    http_method="POST", endpoint_pattern="/issue/{issue_id_or_key}/comment",
                    parameters=[
                        _p("issue_id_or_key", desc="Issue key", example="SEC-123"),
                        _p("body", desc="Comment text"),
                    ],
                ),
                ProductAction(
                    id="transition_issue", name="Transition Issue",
                    description="Move a Jira issue to a different status (e.g., In Progress, Done).",
                    http_method="POST", endpoint_pattern="/issue/{issue_id_or_key}/transitions",
                    parameters=[
                        _p("issue_id_or_key", desc="Issue key"),
                        _p("transition_id", desc="Target transition ID"),
                    ],
                ),
            ],
        ),
    ]


# ============================================================================
# Global Catalog Instance
# ============================================================================

product_catalog = ProductCatalog()
