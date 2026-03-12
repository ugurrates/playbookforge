"""
PlaybookForge - Base Importer
Abstract base class for all SOAR platform importers.
"""

from abc import ABC, abstractmethod
from typing import Any

from ..core.cacao_model import CacaoPlaybook


class BaseImporter(ABC):
    """Base class for converting vendor-specific formats to CACAO playbooks"""

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
    def supported_extensions(self) -> list[str]:
        """Supported file extensions (e.g., ['.yml', '.yaml'])"""
        ...

    @abstractmethod
    def detect(self, content: str) -> bool:
        """Auto-detect if content matches this platform's format"""
        ...

    @abstractmethod
    def parse(self, content: str) -> CacaoPlaybook:
        """Parse vendor format and return a CACAO playbook"""
        ...

    def get_metadata(self) -> dict[str, Any]:
        """Return importer metadata"""
        return {
            "platform_name": self.platform_name,
            "platform_id": self.platform_id,
            "supported_extensions": self.supported_extensions,
        }
