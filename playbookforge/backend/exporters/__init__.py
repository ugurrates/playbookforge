"""
PlaybookForge - Exporter Registry
Central registry for all platform exporters. Also re-exports for convenience.
"""

from ..core.cacao_model import CacaoPlaybook
from .base import BaseExporter
from .xsoar_exporter import XSOARExporter
from .shuffle_exporter import ShuffleExporter
from .sentinel_fortisoar_exporter import SentinelExporter, FortiSOARExporter
from .splunk_soar_exporter import SplunkSOARExporter
from .google_secops_exporter import GoogleSecOpsExporter


class ExporterRegistry:
    """Registry of all available exporters"""

    _exporters: dict[str, BaseExporter] = {}

    def __init__(self):
        # Register built-in exporters
        self.register(XSOARExporter())
        self.register(ShuffleExporter())
        self.register(SentinelExporter())
        self.register(FortiSOARExporter())
        self.register(SplunkSOARExporter())
        self.register(GoogleSecOpsExporter())

    def register(self, exporter: BaseExporter) -> None:
        self._exporters[exporter.platform_id] = exporter

    def get(self, platform_id: str) -> BaseExporter | None:
        return self._exporters.get(platform_id)

    def list_platforms(self) -> list[dict[str, str]]:
        return [e.get_metadata() for e in self._exporters.values()]

    def export(self, playbook: CacaoPlaybook, platform_id: str) -> str:
        exporter = self.get(platform_id)
        if not exporter:
            available = ", ".join(self._exporters.keys())
            raise ValueError(f"Unknown platform '{platform_id}'. Available: {available}")
        return exporter.export(playbook)

    def export_all(self, playbook: CacaoPlaybook) -> dict[str, str]:
        """Export playbook to all supported platforms"""
        results = {}
        for pid, exporter in self._exporters.items():
            try:
                results[pid] = exporter.export(playbook)
            except Exception as e:
                results[pid] = f"ERROR: {str(e)}"
        return results


# Global registry instance
registry = ExporterRegistry()
