"""
PlaybookForge — Community Playbook Repository Manager.

Automatically fetches playbooks from public GitHub repositories,
imports them via the existing importer pipeline, and stores them
in the local library.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPOS_DIR = Path(__file__).parent.parent.parent / "repos"
REPO_STATE_FILE = REPOS_DIR / "_state.json"


class RepoStatus(str, Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    ERROR = "error"


@dataclass
class RepoConfig:
    """A community playbook repository definition."""
    id: str
    name: str
    url: str
    platform: str  # xsoar | shuffle | sentinel | fortisoar | multi
    description: str
    branch: str = "main"
    playbook_paths: list[str] = field(default_factory=list)
    file_patterns: list[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "platform": self.platform,
            "description": self.description,
            "branch": self.branch,
            "playbook_paths": self.playbook_paths,
            "file_patterns": self.file_patterns,
            "enabled": self.enabled,
        }


@dataclass
class RepoState:
    """Runtime state for a repo."""
    repo_id: str
    status: RepoStatus = RepoStatus.PENDING
    last_sync: Optional[str] = None
    playbooks_imported: int = 0
    playbooks_failed: int = 0
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "repo_id": self.repo_id,
            "status": self.status.value,
            "last_sync": self.last_sync,
            "playbooks_imported": self.playbooks_imported,
            "playbooks_failed": self.playbooks_failed,
            "error_message": self.error_message,
        }


# ---------------------------------------------------------------------------
# Built-in repository definitions
# ---------------------------------------------------------------------------

BUILTIN_REPOS: list[RepoConfig] = [
    RepoConfig(
        id="demisto-content",
        name="Cortex XSOAR Content",
        url="https://github.com/demisto/content.git",
        platform="xsoar",
        description="Official Palo Alto XSOAR content packs — 800+ playbooks",
        branch="master",
        playbook_paths=["Packs/*/Playbooks"],
        file_patterns=["*.yml"],
    ),
    RepoConfig(
        id="azure-sentinel",
        name="Microsoft Sentinel Playbooks",
        url="https://github.com/Azure/Azure-Sentinel.git",
        platform="sentinel",
        description="Official Microsoft Sentinel playbooks — 484 playbooks from 195 providers",
        branch="master",
        playbook_paths=["Playbooks", "Solutions/*/Playbooks"],
        file_patterns=["azuredeploy.json"],
    ),
    RepoConfig(
        id="shuffle-workflows",
        name="Shuffle Workflows",
        url="https://github.com/Shuffle/workflows.git",
        platform="shuffle",
        description="Official Shuffle SOAR community workflows",
        branch="master",
        playbook_paths=["."],
        file_patterns=["*.json"],
    ),
    RepoConfig(
        id="awesome-playbooks",
        name="Awesome Playbooks",
        url="https://github.com/luduslibrum/awesome-playbooks.git",
        platform="multi",
        description="Multi-platform community playbook collection (XSOAR, Shuffle, Sentinel)",
        branch="main",
        playbook_paths=["."],
        file_patterns=["*.yml", "*.yaml", "*.json"],
    ),
]

# FortiSOAR has many separate repos — we handle them specially
FORTISOAR_SOLUTION_PACKS = [
    "solution-pack-soar-framework",
    "solution-pack-mitre-attack-threat-hunting",
    "solution-pack-outbreak-response-framework",
    "solution-pack-soc-simulator",
    "solution-pack-incident-response",
    "solution-pack-phishing-email-management",
    "solution-pack-vulnerability-management",
    "solution-pack-compliance-management",
]

for pack_name in FORTISOAR_SOLUTION_PACKS:
    BUILTIN_REPOS.append(
        RepoConfig(
            id=f"fortisoar-{pack_name}",
            name=f"FortiSOAR {pack_name.replace('solution-pack-', '').replace('-', ' ').title()}",
            url=f"https://github.com/fortinet-fortisoar/{pack_name}.git",
            platform="fortisoar",
            description=f"Fortinet FortiSOAR official solution pack: {pack_name}",
            branch="develop",
            playbook_paths=["playbooks"],
            file_patterns=["*.json"],
        )
    )


# ---------------------------------------------------------------------------
# Repo Manager
# ---------------------------------------------------------------------------

class RepoManager:
    """Manages cloning, syncing, and importing playbooks from community repos."""

    def __init__(self) -> None:
        REPOS_DIR.mkdir(parents=True, exist_ok=True)
        self._repos: dict[str, RepoConfig] = {r.id: r for r in BUILTIN_REPOS}
        self._states: dict[str, RepoState] = {}
        self._lock = threading.Lock()
        self._sync_thread: Optional[threading.Thread] = None
        self._load_state()

    def _load_state(self) -> None:
        """Load persisted sync state."""
        if REPO_STATE_FILE.exists():
            try:
                with open(REPO_STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for repo_id, state_data in data.items():
                    self._states[repo_id] = RepoState(
                        repo_id=repo_id,
                        status=RepoStatus(state_data.get("status", "pending")),
                        last_sync=state_data.get("last_sync"),
                        playbooks_imported=state_data.get("playbooks_imported", 0),
                        playbooks_failed=state_data.get("playbooks_failed", 0),
                        error_message=state_data.get("error_message", ""),
                    )
            except Exception as e:
                logger.warning("Failed to load repo state: %s", e)

    def _save_state(self) -> None:
        """Persist sync state to disk."""
        with self._lock:
            try:
                data = {rid: s.to_dict() for rid, s in self._states.items()}
                tmp = REPO_STATE_FILE.with_suffix(".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                tmp.replace(REPO_STATE_FILE)
            except Exception as e:
                logger.error("Failed to save repo state: %s", e)

    # -- Public API --

    def list_repos(self) -> list[dict]:
        """Return all repos with their current state."""
        results = []
        for repo_id, repo in self._repos.items():
            state = self._states.get(repo_id, RepoState(repo_id=repo_id))
            info = repo.to_dict()
            info.update(state.to_dict())
            results.append(info)
        return results

    def get_repo(self, repo_id: str) -> dict | None:
        repo = self._repos.get(repo_id)
        if not repo:
            return None
        state = self._states.get(repo_id, RepoState(repo_id=repo_id))
        info = repo.to_dict()
        info.update(state.to_dict())
        return info

    def sync_all(self, background: bool = True) -> dict:
        """Start syncing all enabled repos. Returns immediately if background=True."""
        if self._sync_thread and self._sync_thread.is_alive():
            return {"status": "already_syncing", "message": "A sync is already in progress"}

        enabled = [r for r in self._repos.values() if r.enabled]
        if background:
            self._sync_thread = threading.Thread(
                target=self._sync_repos, args=(enabled,), daemon=True
            )
            self._sync_thread.start()
            return {"status": "started", "repos": len(enabled)}
        else:
            return self._sync_repos(enabled)

    def sync_repo(self, repo_id: str) -> dict:
        """Sync a single repo in the background."""
        repo = self._repos.get(repo_id)
        if not repo:
            return {"status": "error", "message": f"Repo '{repo_id}' not found"}
        t = threading.Thread(target=self._sync_repos, args=([repo],), daemon=True)
        t.start()
        return {"status": "started", "repo_id": repo_id}

    def toggle_repo(self, repo_id: str, enabled: bool) -> dict:
        """Enable or disable a repo."""
        repo = self._repos.get(repo_id)
        if not repo:
            return {"status": "error", "message": f"Repo '{repo_id}' not found"}
        repo.enabled = enabled
        return {"status": "ok", "repo_id": repo_id, "enabled": enabled}

    def get_sync_status(self) -> dict:
        """Overall sync status."""
        total = len(self._repos)
        synced = sum(1 for s in self._states.values() if s.status == RepoStatus.SYNCED)
        errors = sum(1 for s in self._states.values() if s.status == RepoStatus.ERROR)
        syncing = sum(1 for s in self._states.values() if s.status == RepoStatus.SYNCING)
        total_imported = sum(s.playbooks_imported for s in self._states.values())
        return {
            "total_repos": total,
            "synced": synced,
            "syncing": syncing,
            "errors": errors,
            "pending": total - synced - errors - syncing,
            "total_playbooks_imported": total_imported,
            "is_syncing": self._sync_thread is not None and self._sync_thread.is_alive(),
        }

    # -- Internal sync logic --

    def _sync_repos(self, repos: list[RepoConfig]) -> dict:
        """Clone/pull repos and import playbooks."""
        from ..importers import importer_registry
        from ..db.library import library, PlaybookEntry

        total_imported = 0
        total_failed = 0

        for repo in repos:
            state = self._states.setdefault(repo.id, RepoState(repo_id=repo.id))
            state.status = RepoStatus.SYNCING
            state.error_message = ""
            self._save_state()

            try:
                repo_dir = self._clone_or_pull(repo)
                imported, failed = self._scan_and_import(
                    repo, repo_dir, importer_registry, library, PlaybookEntry
                )
                state.status = RepoStatus.SYNCED
                state.playbooks_imported = imported
                state.playbooks_failed = failed
                state.last_sync = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
                total_imported += imported
                total_failed += failed
                logger.info("Synced %s: %d imported, %d failed", repo.id, imported, failed)
            except Exception as e:
                state.status = RepoStatus.ERROR
                state.error_message = str(e)[:500]
                logger.error("Failed to sync %s: %s", repo.id, e)

            self._save_state()

        return {
            "status": "completed",
            "total_imported": total_imported,
            "total_failed": total_failed,
        }

    def _clone_or_pull(self, repo: RepoConfig) -> Path:
        """Clone if missing, pull if exists. Uses shallow clone for speed."""
        repo_dir = REPOS_DIR / repo.id

        if (repo_dir / ".git").exists():
            # Pull latest
            logger.info("Pulling %s ...", repo.id)
            try:
                subprocess.run(
                    ["git", "pull", "--ff-only"],
                    cwd=repo_dir, capture_output=True, text=True,
                    timeout=300,
                )
            except Exception as e:
                logger.warning("Pull failed for %s, re-cloning: %s", repo.id, e)
                shutil.rmtree(repo_dir, ignore_errors=True)
                return self._clone_or_pull(repo)
        else:
            # Shallow clone (depth=1 for speed, --filter for sparse)
            logger.info("Cloning %s (shallow) ...", repo.id)
            repo_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                "git", "clone",
                "--depth", "1",
                "--branch", repo.branch,
                "--single-branch",
                repo.url,
                str(repo_dir),
            ]

            # For large repos, use sparse checkout if playbook_paths are specific
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600,
            )
            if result.returncode != 0:
                raise RuntimeError(f"git clone failed: {result.stderr[:300]}")

        return repo_dir

    def _scan_and_import(
        self,
        repo: RepoConfig,
        repo_dir: Path,
        importer_registry,
        library,
        PlaybookEntry,
    ) -> tuple[int, int]:
        """Scan a cloned repo for playbook files and import them."""
        imported = 0
        failed = 0

        # Collect all candidate files
        candidates = self._find_playbook_files(repo, repo_dir)
        logger.info("Found %d candidate files in %s", len(candidates), repo.id)

        for filepath in candidates:
            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
                if not content.strip():
                    continue

                # Determine platform
                platform_id = repo.platform if repo.platform != "multi" else None

                # Try to detect and parse
                if platform_id:
                    importer = importer_registry.get(platform_id)
                    if not importer:
                        continue
                    if not importer.detect(content):
                        continue
                else:
                    importer = importer_registry.detect(content)
                    if not importer:
                        continue

                playbook = importer.parse(content)

                # Build library entry
                rel_path = str(filepath.relative_to(repo_dir)).replace("\\", "/")
                entry_id = f"lib-{importer.platform_id}-{uuid.uuid4().hex[:12]}"

                # Extract MITRE techniques from external_references
                mitre = []
                pb_dict = playbook.model_dump(mode="json", exclude_none=True)
                for ref in pb_dict.get("external_references", []):
                    name = ref.get("name", "")
                    if name.startswith("T") and name[1:].replace(".", "").isdigit():
                        mitre.append(name)

                # Count action steps
                action_count = sum(
                    1 for s in pb_dict.get("workflow", {}).values()
                    if s.get("type") == "action"
                )

                entry = PlaybookEntry(
                    id=entry_id,
                    name=playbook.name or filepath.stem,
                    description=playbook.description or f"Imported from {repo.name}",
                    source_platform=importer.platform_id,
                    source_repo=repo.name,
                    source_file=rel_path,
                    playbook_types=[pt.value if hasattr(pt, 'value') else str(pt) for pt in (playbook.playbook_types or [])],
                    step_count=len(pb_dict.get("workflow", {})),
                    action_count=action_count,
                    tags=[repo.id, importer.platform_id],
                    mitre_techniques=mitre,
                    cacao_playbook=pb_dict,
                )

                # Check if already imported (by source_file + source_repo)
                existing = library.list_all(search=rel_path, limit=1)
                if existing["total"] > 0:
                    # Skip duplicates based on source file name
                    for e in existing["playbooks"]:
                        if e.get("source_file") == rel_path and e.get("source_repo") == repo.name:
                            continue
                    # Not exact match, import it
                    pass

                library.add(entry)
                imported += 1

            except Exception as e:
                failed += 1
                if failed <= 5:
                    logger.debug("Failed to import %s: %s", filepath.name, str(e)[:200])

        return imported, failed

    def _find_playbook_files(self, repo: RepoConfig, repo_dir: Path) -> list[Path]:
        """Find playbook files matching the repo's path and pattern config."""
        candidates: list[Path] = []

        for search_path in repo.playbook_paths:
            for pattern in repo.file_patterns:
                # Handle glob patterns in search_path (e.g., "Packs/*/Playbooks")
                if "*" in search_path:
                    full_pattern = f"{search_path}/{pattern}"
                    for p in repo_dir.glob(full_pattern):
                        if p.is_file() and self._is_candidate(p):
                            candidates.append(p)
                else:
                    search_dir = repo_dir / search_path
                    if search_dir.exists():
                        for p in search_dir.rglob(pattern):
                            if p.is_file() and self._is_candidate(p):
                                candidates.append(p)

        # Deduplicate
        return list(dict.fromkeys(candidates))

    @staticmethod
    def _is_candidate(path: Path) -> bool:
        """Quick filter: skip obviously non-playbook files."""
        name = path.name.lower()
        # Skip common non-playbook files
        skip_names = {
            "readme.md", "readme.rst", "license", "license.md",
            "changelog.md", "contributing.md", ".gitignore",
            "package.json", "package-lock.json", "node_modules",
            "requirements.txt", "setup.py", "setup.cfg",
            "dockerfile", "docker-compose.yml",
            "conftest.py", "pytest.ini", "tox.ini",
            "_index.json", "_metadata.json", "_state.json",
        }
        if name in skip_names:
            return False
        # Skip test files and config files
        if name.startswith("test_") or name.startswith("."):
            return False
        # Skip very small files (likely not playbooks)
        try:
            if path.stat().st_size < 100:
                return False
            # Skip very large files (>5MB, likely not individual playbooks)
            if path.stat().st_size > 5_000_000:
                return False
        except OSError:
            return False
        return True


# Global instance
repo_manager = RepoManager()
