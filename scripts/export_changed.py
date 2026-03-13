#!/usr/bin/env python3
"""Export only playbooks that changed in the current PR (vs origin/main)."""

import sys
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playbookforge.backend.core.cacao_model import CacaoPlaybook
from playbookforge.backend.exporters import registry

TARGET_PLATFORMS = ["xsoar", "sentinel", "shuffle", "fortisoar"]


def get_changed_playbooks() -> list[Path]:
    """Get list of changed playbook JSON files compared to origin/main."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main", "--", "playbooks/"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        files = [
            PROJECT_ROOT / f.strip()
            for f in result.stdout.strip().splitlines()
            if f.strip().endswith(".json")
        ]
        return [f for f in files if f.exists()]
    except Exception as e:
        print(f"WARNING: git diff failed ({e}), falling back to all playbooks")
        return sorted((PROJECT_ROOT / "playbooks").glob("**/*.json"))


def main() -> int:
    changed = get_changed_playbooks()

    if not changed:
        print("No changed playbooks detected. Nothing to export.")
        return 0

    exports_dir = PROJECT_ROOT / "exports"
    errors = 0

    print(f"Exporting {len(changed)} changed playbook(s)...\n")

    for path in changed:
        rel = path.relative_to(PROJECT_ROOT)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            playbook = CacaoPlaybook(**data)
            stem = path.stem

            for platform_id in TARGET_PLATFORMS:
                exporter = registry.get(platform_id)
                if not exporter:
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

    print(f"\nDone. Errors: {errors}")
    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
