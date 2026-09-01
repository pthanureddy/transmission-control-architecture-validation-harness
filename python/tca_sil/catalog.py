"""Load and validate deterministic scenario definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict, cast


class SignalValues(TypedDict, total=False):
    vehicle_speed_kph: float
    input_shaft_rpm: float
    output_shaft_rpm: float
    throttle_primary_pct: float
    throttle_redundant_pct: float
    direction_request: str
    brake_applied: bool


class ScenarioStep(TypedDict, total=False):
    sequence: int
    driver_sequence: int
    reception_timestamp_ms: int
    now_ms: int
    execution_time_us: int
    order: list[str]
    fault: str
    fault_target: str
    signals: SignalValues


class ScenarioExpected(TypedDict, total=False):
    statuses: list[str]
    output_count: int
    mode: str
    fault: str
    gear: str
    torque_limit_pct: int
    shift_inhibited: bool
    active_dtc: str


class ScenarioSpec(TypedDict):
    id: str
    title: str
    requirements: list[str]
    steps: list[ScenarioStep]
    expected: ScenarioExpected


def default_catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "scenarios" / "catalog.json"


def load_catalog(path: Path | None = None) -> dict[str, ScenarioSpec]:
    catalog_path = path or default_catalog_path()
    raw = cast(dict[str, object], json.loads(catalog_path.read_text(encoding="utf-8")))
    scenarios = cast(list[ScenarioSpec], raw.get("scenarios"))
    if not scenarios:
        raise ValueError("Scenario catalog must contain at least one scenario")
    result: dict[str, ScenarioSpec] = {}
    for scenario in scenarios:
        scenario_id = scenario.get("id", "")
        if not scenario_id or scenario_id in result:
            raise ValueError(f"Scenario ID must be non-empty and unique: {scenario_id!r}")
        if not scenario.get("requirements") or not scenario.get("steps"):
            raise ValueError(f"Scenario {scenario_id} lacks requirements or steps")
        result[scenario_id] = scenario
    return result
