#!/usr/bin/env python3
"""Export all CACAO playbooks to all supported SOAR platforms."""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playbookforge.backend.core.cacao_model import CacaoPlaybook
from playbookforge.backend.exporters import registry

TARGET_PLATFORMS = ["xsoar", "sentinel", "shuffle", "fortisoar"]


def main() -> int:
    playbooks_dir = PROJECT_ROOT / "playbooks"
    exports_dir = PROJECT_ROOT / "exports"

    if not playbooks_dir.exists():
        print("ERROR: playbooks/ directory not found")
        return 1

    json_files = sorted(playbooks_dir.glob("**/*.json"))
    if not json_files:
        print("No JSON files found in playbooks/")
        return 0

    print(f"Exporting {len(json_files)} playbook(s) to {len(TARGET_PLATFORMS)} platforms...\n")

    errors = 0

    for path in json_files:
        rel = path.relative_to(PROJECT_ROOT)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            playbook = CacaoPlaybook(**data)
            stem = path.stem

            for platform_id in TARGET_PLATFORMS:
                exporter = registry.get(platform_id)
                if not exporter:
                    print(f"  SKIP  {platform_id} — exporter not found")
                    continue

                out_dir = exports_dir / platform_id
                out_dir.mkdir(parents=True, exist_ok=True)

                try:
                    content = exporter.export(playbook)
                    ext = exporter.file_extension
                    out_file = out_dir / f"{stem}{ext}"

                    with open(out_file, "w", encoding="utf-8") as f:
                        f.write(content)

                    print(f"  OK    {platform_id}/{stem}{ext}")
                except Exception as e:
                    print(f"  FAIL  {platform_id}/{stem} — {e}")
                    errors += 1

        except Exception as e:
            print(f"  FAIL  {rel} — {type(e).__name__}: {e}")
            errors += 1

    print(f"\nExport complete. Errors: {errors}")
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
