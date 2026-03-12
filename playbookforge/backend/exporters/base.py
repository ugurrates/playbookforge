"""
PlaybookForge - Base Exporter
Abstract base class for all SOAR platform exporters.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..core.cacao_model import CacaoPlaybook


class BaseExporter(ABC):
    """Base class for converting CACAO playbooks to vendor-specific formats"""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name"""
        ...

    @property
    @abstractmethod
    def platform_id(self) -> str:
        """Machine-readable platform identifier"""
        ...

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Output file extension (e.g., '.yml', '.json', '.py')"""
        ...

    @abstractmethod
    def export(self, playbook: CacaoPlaybook) -> str:
        """Convert a CACAO playbook to the vendor format string"""
        ...

    def export_to_dict(self, playbook: CacaoPlaybook) -> dict[str, Any]:
        """Convert to dict (override for JSON-based formats)"""
        import json
        return json.loads(self.export(playbook))

    def get_filename(self, playbook: CacaoPlaybook) -> str:
        """Generate an appropriate filename for the exported playbook"""
        safe_name = playbook.name.lower().replace(" ", "_").replace("/", "_")[:64]
        return f"{safe_name}{self.file_extension}"

    def get_metadata(self) -> dict[str, str]:
        """Return exporter metadata"""
        return {
            "platform_name": self.platform_name,
            "platform_id": self.platform_id,
            "file_extension": self.file_extension,
        }
