"""
Batch import script — Import playbooks from awesome-playbooks repo into PlaybookForge library.
Converts vendor-format playbooks to CACAO v2.0 and stores them in the library.

Usage:
    python -m scripts.import_awesome_playbooks [--source PATH] [--limit N]
"""

from __future__ import annotations

import json
import logging
import os
import sys
import traceback
import uuid
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.importers import importer_registry
from backend.db.library import PlaybookLibrary, PlaybookEntry

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Platform mapping: awesome-playbooks folder → our platform_id
PLATFORM_MAP = {
    "xsoar": "xsoar",
    "demisto": "xsoar",  # Demisto = old name for XSOAR
    "shuffle": "shuffle",
    "ms_azure": "sentinel",
    "fortinet": "fortisoar",
}

# File extensions per platform
EXTENSION_MAP = {
    "xsoar": [".yml", ".yaml"],
    "shuffle": [".json"],
    "sentinel": [".json"],
    "fortisoar": [".json"],
}


def extract_tags_from_name(name: str) -> list[str]:
    """Extract useful tags from playbook name."""
    tags = []
    keywords = {
        "phishing": "phishing",
        "malware": "malware",
        "ransomware": "ransomware",
        "brute": "brute-force",
        "brute-force": "brute-force",
        "enrichment": "enrichment",
        "investigation": "investigation",
        "remediation": "remediation",
        "response": "incident-response",
        "incident": "incident-response",
        "threat": "threat-hunting",
        "hunt": "threat-hunting",
        "ioc": "ioc",
        "indicator": "indicator",
        "block": "blocking",
        "quarantine": "quarantine",
        "isolat": "isolation",
        "email": "email",
        "endpoint": "endpoint",
        "network": "network",
        "firewall": "firewall",
        "dns": "dns",
        "ip": "ip-address",
        "url": "url",
        "hash": "hash",
        "domain": "domain",
        "alert": "alert",
        "triage": "triage",
        "escalat": "escalation",
        "notify": "notification",
        "report": "reporting",
        "forensic": "forensics",
        "contain": "containment",
        "eradicat": "eradication",
        "recovery": "recovery",
        "vulnerability": "vulnerability",
        "scan": "scanning",
        "dedup": "deduplication",
        "pcap": "pcap",
        "sandbox": "sandbox",
        "detonate": "detonation",
        "xdr": "xdr",
        "edr": "edr",
        "siem": "siem",
        "active directory": "active-directory",
        "ad ": "active-directory",
        "azure": "azure",
        "aws": "aws",
        "gcp": "gcp",
    }
    name_lower = name.lower()
    for keyword, tag in keywords.items():
        if keyword in name_lower and tag not in tags:
            tags.append(tag)
    return tags


def extract_mitre_from_playbook(playbook_dict: dict) -> list[str]:
    """Extract MITRE technique IDs from a CACAO playbook."""
    techniques = []
    for ref in playbook_dict.get("external_references", []):
        ext_id = ref.get("external_id", "")
        if ext_id.startswith("T") and ext_id[1:].replace(".", "").isdigit():
            techniques.append(ext_id)
    return techniques


def infer_playbook_types(name: str, description: str) -> list[str]:
    """Infer CACAO playbook_types from name and description."""
    text = f"{name} {description}".lower()
    types = []
    if any(w in text for w in ["investigat", "triage", "analyz", "enrich"]):
        types.append("investigation")
    if any(w in text for w in ["response", "incident", "remediat", "eradicat"]):
        types.append("remediation")
    if any(w in text for w in ["detect", "alert", "monitor", "hunt"]):
        types.append("detection")
    if any(w in text for w in ["prevent", "block", "contain", "isolat", "quarantin"]):
        types.append("prevention")
    if any(w in text for w in ["notify", "report", "escalat", "communicat"]):
        types.append("notification")
    if any(w in text for w in ["mitigat"]):
        types.append("mitigation")
    if not types:
        types.append("investigation")
    return types


def import_playbooks(
    source_dir: Path,
    library: PlaybookLibrary,
    limit: int = 0,
) -> dict:
    """Import playbooks from awesome-playbooks directory structure."""
    stats = {
        "total_found": 0,
        "imported": 0,
        "skipped": 0,
        "failed": 0,
        "by_platform": {},
        "errors": [],
    }

    for folder_name, platform_id in PLATFORM_MAP.items():
        platform_dir = source_dir / folder_name
        if not platform_dir.exists():
            logger.info("Skipping %s — directory not found", folder_name)
            continue

        extensions = EXTENSION_MAP.get(platform_id, [".json", ".yml"])
        files = []
        for ext in extensions:
            files.extend(platform_dir.rglob(f"*{ext}"))

        # Filter out non-playbook files
        files = [f for f in files if _is_playbook_file(f, platform_id)]

        platform_count = 0
        logger.info("Found %d candidate files in %s/ (platform: %s)", len(files), folder_name, platform_id)

        for filepath in files:
            if limit > 0 and stats["imported"] >= limit:
                break

            stats["total_found"] += 1

            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")

                # Try to import via our importer
                importer = importer_registry.get(platform_id)
                if not importer:
                    stats["skipped"] += 1
                    continue

                # Check if importer can detect this format
                if not importer.detect(content):
                    stats["skipped"] += 1
                    continue

                # Parse to CACAO
                cacao_playbook = importer.parse(content)
                playbook_dict = cacao_playbook.model_dump(exclude_none=True)

                # Build entry
                name = cacao_playbook.name or filepath.stem.replace("_", " ").replace("-", " ")
                description = cacao_playbook.description or ""

                # Count steps
                step_count = len(cacao_playbook.workflow)
                action_count = sum(
                    1 for s in cacao_playbook.workflow.values()
                    if s.type == "action"
                )

                tags = extract_tags_from_name(name)
                tags.append(platform_id)
                mitre = extract_mitre_from_playbook(playbook_dict)
                pb_types = infer_playbook_types(name, description)

                entry_id = f"lib-{platform_id}-{uuid.uuid4().hex[:12]}"
                entry = PlaybookEntry(
                    id=entry_id,
                    name=name,
                    description=description[:500] if description else f"Imported from {folder_name}",
                    source_platform=platform_id,
                    source_repo="luduslibrum/awesome-playbooks",
                    source_file=str(filepath.relative_to(source_dir)),
                    playbook_types=pb_types,
                    step_count=step_count,
                    action_count=action_count,
                    tags=list(set(tags)),
                    mitre_techniques=mitre,
                    cacao_playbook=playbook_dict,
                )

                library.add(entry)
                stats["imported"] += 1
                platform_count += 1

            except Exception as e:
                stats["failed"] += 1
                if len(stats["errors"]) < 20:  # Keep first 20 errors
                    stats["errors"].append({
                        "file": str(filepath.relative_to(source_dir)),
                        "error": str(e)[:200],
                    })

        stats["by_platform"][platform_id] = stats["by_platform"].get(platform_id, 0) + platform_count
        logger.info("  → Imported %d from %s", platform_count, folder_name)

    return stats


def _is_playbook_file(filepath: Path, platform_id: str) -> bool:
    """Filter out non-playbook files (images, readmes, etc.)."""
    name = filepath.name.lower()

    # Skip common non-playbook files
    skip_patterns = [
        "readme", "changelog", "license", "contributing",
        ".png", ".jpg", ".gif", ".svg", ".ico",
        ".md", ".txt", ".ps1", ".ps1xml", ".psm1",
        "__pycache__", ".pyc",
    ]
    for pattern in skip_patterns:
        if pattern in name:
            return False

    # For Sentinel, only look for azuredeploy.json or files in Playbooks dirs
    if platform_id == "sentinel":
        if "azuredeploy" in name or "playbook" in str(filepath).lower():
            return True
        return False

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Import awesome-playbooks into PlaybookForge library")
    parser.add_argument("--source", type=str, default=None, help="Path to awesome-playbooks/playbooks/")
    parser.add_argument("--limit", type=int, default=0, help="Max playbooks to import (0 = unlimited)")
    parser.add_argument("--library-dir", type=str, default=None, help="Library storage directory")
    args = parser.parse_args()

    # Find source directory
    if args.source:
        source_dir = Path(args.source)
    else:
        # Try to find awesome-playbooks relative to project
        candidates = [
            PROJECT_ROOT.parent / "awesome-playbooks" / "playbooks",
            PROJECT_ROOT / "awesome-playbooks" / "playbooks",
            Path("awesome-playbooks") / "playbooks",
        ]
        source_dir = None
        for c in candidates:
            if c.exists():
                source_dir = c
                break
        if not source_dir:
            logger.error("Could not find awesome-playbooks/playbooks/ directory. Use --source to specify.")
            sys.exit(1)

    logger.info("Source: %s", source_dir)

    # Create library
    lib_dir = Path(args.library_dir) if args.library_dir else None
    library = PlaybookLibrary(lib_dir)
    logger.info("Library: %s (existing: %d playbooks)", library.library_dir, library.count())

    # Import
    stats = import_playbooks(source_dir, library, limit=args.limit)

    # Report
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)
    print(f"  Total files found:  {stats['total_found']}")
    print(f"  Successfully imported:  {stats['imported']}")
    print(f"  Skipped (not matching):  {stats['skipped']}")
    print(f"  Failed:  {stats['failed']}")
    print(f"\n  By platform:")
    for platform, count in sorted(stats["by_platform"].items()):
        print(f"    {platform}: {count}")
    print(f"\n  Library total: {library.count()} playbooks")

    if stats["errors"]:
        print(f"\n  First {len(stats['errors'])} errors:")
        for err in stats["errors"][:10]:
            print(f"    {err['file']}: {err['error'][:100]}")


if __name__ == "__main__":
    main()
