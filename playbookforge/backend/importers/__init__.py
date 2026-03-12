"""
PlaybookForge - Importer Registry
Central registry for all platform importers.
"""

from ..core.cacao_model import CacaoPlaybook
from .base import BaseImporter
from .auto_detect import auto_detect
from .xsoar_importer import XSOARImporter
from .shuffle_importer import ShuffleImporter
from .sentinel_importer import SentinelImporter
from .fortisoar_importer import FortiSOARImporter


class ImporterRegistry:
    """Registry of all available importers"""

    _importers: list[BaseImporter]

    def __init__(self) -> None:
        self._importers = []
        self.register(XSOARImporter())
        self.register(ShuffleImporter())
        self.register(SentinelImporter())
        self.register(FortiSOARImporter())

    def register(self, importer: BaseImporter) -> None:
        self._importers.append(importer)

    def get(self, platform_id: str) -> BaseImporter | None:
        for imp in self._importers:
            if imp.platform_id == platform_id:
                return imp
        return None

    def list_platforms(self) -> list[dict[str, str]]:
        return [imp.get_metadata() for imp in self._importers]

    def detect(self, content: str) -> BaseImporter | None:
        """Auto-detect the platform from file content."""
        return auto_detect(content, self._importers)

    def parse(self, content: str, platform_id: str | None = None) -> CacaoPlaybook:
        """Parse vendor content to CACAO. If platform_id is None, auto-detect."""
        if platform_id:
            importer = self.get(platform_id)
            if not importer:
                available = ", ".join(i.platform_id for i in self._importers)
                raise ValueError(f"Unknown platform '{platform_id}'. Available: {available}")
        else:
            importer = self.detect(content)
            if not importer:
                raise ValueError("Could not auto-detect platform format")

        return importer.parse(content)


# Global registry instance
importer_registry = ImporterRegistry()
