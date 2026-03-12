"""
Blue Team Tool Integrations for PlaybookForge.

Connects to external Blue Team tools developed by Ugur Ates:
- Blue-Team-News: Threat intelligence feed (latest CVEs, threats)
- Blue-Team-Assistant: SOC assistant toolkit
- MCP-For-SOC: MCP server for Claude-based SOC automation

All integrations are optional — PlaybookForge works standalone.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class IntegrationStatus:
    """Status of a single integration."""
    name: str
    description: str
    url: str
    connected: bool = False
    version: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "connected": self.connected,
            "version": self.version,
            "error": self.error,
        }


@dataclass
class ThreatItem:
    """A single threat/CVE from Blue-Team-News."""
    id: str
    title: str
    source: str
    severity: str = "medium"
    description: str = ""
    url: str = ""
    published: str = ""
    tags: list[str] = field(default_factory=list)
    cve_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "severity": self.severity,
            "description": self.description,
            "url": self.url,
            "published": self.published,
            "tags": self.tags,
            "cve_ids": self.cve_ids,
        }


class IntegrationClient:
    """Client for Blue Team tool integrations."""

    def __init__(self) -> None:
        self.blue_team_news_url = os.environ.get(
            "BLUE_TEAM_NEWS_URL", "http://localhost:8080"
        )
        self.blue_team_assistant_url = os.environ.get(
            "BLUE_TEAM_ASSISTANT_URL", "http://localhost:8081"
        )
        self.mcp_for_soc_url = os.environ.get(
            "MCP_FOR_SOC_URL", "http://localhost:8082"
        )
        self._timeout = 5.0

    async def check_status(self) -> list[IntegrationStatus]:
        """Check connectivity to all integrations."""
        results: list[IntegrationStatus] = []

        # Blue-Team-News
        news_status = IntegrationStatus(
            name="Blue-Team-News",
            description="Real-time cyber threat intelligence feed with latest CVEs, vulnerabilities, and threat reports",
            url=self.blue_team_news_url,
        )
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self.blue_team_news_url}/api/health")
                if resp.status_code == 200:
                    news_status.connected = True
                    data = resp.json()
                    news_status.version = data.get("version", "unknown")
                else:
                    news_status.error = f"HTTP {resp.status_code}"
        except httpx.ConnectError:
            news_status.error = "Connection refused"
        except Exception as e:
            news_status.error = str(e)
        results.append(news_status)

        # Blue-Team-Assistant
        assistant_status = IntegrationStatus(
            name="Blue-Team-Assistant",
            description="SOC analyst toolkit with IOC analysis, threat hunting queries, and incident response guidance",
            url=self.blue_team_assistant_url,
        )
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self.blue_team_assistant_url}/api/health")
                if resp.status_code == 200:
                    assistant_status.connected = True
                    data = resp.json()
                    assistant_status.version = data.get("version", "unknown")
                else:
                    assistant_status.error = f"HTTP {resp.status_code}"
        except httpx.ConnectError:
            assistant_status.error = "Connection refused"
        except Exception as e:
            assistant_status.error = str(e)
        results.append(assistant_status)

        # MCP-For-SOC
        mcp_status = IntegrationStatus(
            name="MCP-For-SOC",
            description="Model Context Protocol server for Claude-based SOC automation and analysis",
            url=self.mcp_for_soc_url,
        )
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(f"{self.mcp_for_soc_url}/health")
                if resp.status_code == 200:
                    mcp_status.connected = True
                    data = resp.json()
                    mcp_status.version = data.get("version", "unknown")
                else:
                    mcp_status.error = f"HTTP {resp.status_code}"
        except httpx.ConnectError:
            mcp_status.error = "Connection refused"
        except Exception as e:
            mcp_status.error = str(e)
        results.append(mcp_status)

        return results

    async def get_recent_threats(self, limit: int = 10) -> list[ThreatItem]:
        """Fetch recent threats from Blue-Team-News.

        Returns an empty list if the service is not available.
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    f"{self.blue_team_news_url}/api/threats",
                    params={"limit": limit},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("threats", data.get("items", []))
                    return [
                        ThreatItem(
                            id=item.get("id", f"threat-{i}"),
                            title=item.get("title", "Unknown"),
                            source=item.get("source", "Blue-Team-News"),
                            severity=item.get("severity", "medium"),
                            description=item.get("description", ""),
                            url=item.get("url", ""),
                            published=item.get("published", item.get("date", "")),
                            tags=item.get("tags", []),
                            cve_ids=item.get("cve_ids", item.get("cves", [])),
                        )
                        for i, item in enumerate(items[:limit])
                    ]
        except Exception as e:
            logger.debug("Blue-Team-News not available: %s", e)
        return []

    async def get_threat_context(self, indicator: str) -> dict:
        """Get enriched threat context from Blue-Team-Assistant.

        Takes an IOC (IP, hash, domain, CVE ID) and returns analysis.
        Returns empty dict if the service is not available.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self.blue_team_assistant_url}/api/analyze",
                    json={"indicator": indicator},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.debug("Blue-Team-Assistant not available: %s", e)
        return {}

    async def suggest_playbooks(self, cve_id: str) -> list[dict]:
        """Get playbook suggestions for a CVE from Blue-Team-Assistant.

        Returns a list of playbook suggestions with descriptions.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.blue_team_assistant_url}/api/playbook-suggestions",
                    params={"cve": cve_id},
                )
                if resp.status_code == 200:
                    return resp.json().get("suggestions", [])
        except Exception as e:
            logger.debug("Blue-Team-Assistant not available for suggestions: %s", e)
        return []


# Global singleton instance
integration_client = IntegrationClient()
