"""Validate Robot-generated SIL evidence and trace hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    arguments = parser.parse_args()
    manifest_path = arguments.root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    entries = manifest.get("entries", [])
    for entry in entries:
        trace_path = arguments.root / entry["trace"]
        summary_path = arguments.root / entry["summary"]
        if not trace_path.is_file() or not summary_path.is_file():
            failures.append(f"Missing evidence file for {entry['scenario_id']}")
            continue
        actual_hash = hashlib.sha256(trace_path.read_bytes()).hexdigest()
        if actual_hash != entry["trace_sha256"]:
            failures.append(f"Trace hash mismatch for {entry['scenario_id']}")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        if not summary.get("passed"):
            failures.append(f"Scenario did not pass: {entry['scenario_id']}")
    if manifest.get("scenario_count") != len(entries):
        failures.append("Manifest scenario_count does not match entries")
    if manifest.get("passed_count") != len(entries):
        failures.append("Not every manifest entry passed")
    print(
        json.dumps(
            {
                "scenario_count": len(entries),
                "passed_count": manifest.get("passed_count", 0),
                "passed": not failures,
                "failures": failures,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
