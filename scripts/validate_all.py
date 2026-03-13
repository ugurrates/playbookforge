#!/usr/bin/env python3
"""Validate all CACAO playbooks in the playbooks/ directory."""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playbookforge.backend.core.cacao_model import CacaoPlaybook
from playbookforge.backend.core.validator import CacaoValidator


def main() -> int:
    playbooks_dir = PROJECT_ROOT / "playbooks"
    if not playbooks_dir.exists():
        print("ERROR: playbooks/ directory not found")
        return 1

    json_files = sorted(playbooks_dir.glob("**/*.json"))
    if not json_files:
        print("No JSON files found in playbooks/")
        return 0

    validator = CacaoValidator()
    total = len(json_files)
    passed = 0
    failed = 0

    print(f"Validating {total} playbook(s)...\n")

    for path in json_files:
        rel = path.relative_to(PROJECT_ROOT)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            playbook = CacaoPlaybook(**data)
            result = validator.validate(playbook)

            if result.valid:
                print(f"  PASS  {rel}")
                if result.warnings:
                    for w in result.warnings:
                        print(f"        WARN: {w.message}")
                passed += 1
            else:
                print(f"  FAIL  {rel}")
                for err in result.errors:
                    print(f"        ERROR: {err.message}")
                for w in result.warnings:
                    print(f"        WARN: {w.message}")
                failed += 1

        except json.JSONDecodeError as e:
            print(f"  FAIL  {rel}")
            print(f"        Invalid JSON: {e}")
            failed += 1
        except Exception as e:
            print(f"  FAIL  {rel}")
            print(f"        {type(e).__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed, {total} total")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
