"""Fail when SIL requirements, catalog scenarios, and Robot cases drift apart."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "docs" / "sil-requirements.md"
CATALOG = ROOT / "scenarios" / "catalog.json"
ROBOT_SUITE = ROOT / "robot_tests" / "sil_fault_tracing.robot"


def main() -> int:
    requirement_ids = set(re.findall(r"SIL-REQ-\d{3}", REQUIREMENTS.read_text(encoding="utf-8")))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    scenarios = catalog["scenarios"]
    scenario_ids = {scenario["id"] for scenario in scenarios}
    referenced_requirements = {
        requirement for scenario in scenarios for requirement in scenario["requirements"]
    }
    robot_text = ROBOT_SUITE.read_text(encoding="utf-8")
    robot_scenarios = set(re.findall(r"Run SIL Scenario\s+(SIL-(?!REQ)[A-Z]+-\d{3})", robot_text))

    failures: list[str] = []
    if not requirement_ids:
        failures.append("No SIL requirement IDs were found")
    unknown = referenced_requirements - requirement_ids
    uncovered = requirement_ids - referenced_requirements
    missing_robot = scenario_ids - robot_scenarios
    unknown_robot = robot_scenarios - scenario_ids
    if unknown:
        failures.append(f"Catalog references unknown requirements: {sorted(unknown)}")
    if uncovered:
        failures.append(f"Requirements without catalog scenarios: {sorted(uncovered)}")
    if missing_robot:
        failures.append(f"Catalog scenarios absent from Robot suite: {sorted(missing_robot)}")
    if unknown_robot:
        failures.append(f"Robot suite references unknown scenarios: {sorted(unknown_robot)}")

    summary = {
        "requirements": len(requirement_ids),
        "catalog_scenarios": len(scenario_ids),
        "robot_scenarios": len(robot_scenarios),
        "passed": not failures,
        "failures": failures,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
