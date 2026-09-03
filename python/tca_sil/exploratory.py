"""Deterministic boundary probes for a time-boxed exploratory SIL session."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from tca_sil.bridge import DutAdapter
from tca_sil.catalog import ScenarioStep
from tca_sil.codec import CanCodec
from tca_sil.harness import ScenarioHarness, ScenarioOutcome


@dataclass(frozen=True, slots=True)
class BoundaryProbe:
    probe_id: str
    dimension: str
    value: float
    unit: str
    steps: tuple[ScenarioStep, ...]


@dataclass(frozen=True, slots=True)
class BoundaryObservation:
    probe_id: str
    dimension: str
    value: float
    unit: str
    mode: str | None
    fault: str | None
    gear: str | None
    deterministic: bool
    invariant_failures: tuple[str, ...]
    trace_sha256: str


@dataclass(frozen=True, slots=True)
class CampaignResult:
    status: str
    probe_count: int
    execution_count: int
    anomaly_count: int
    observations: tuple[BoundaryObservation, ...]
    json_report: Path
    markdown_report: Path


def boundary_probes() -> tuple[BoundaryProbe, ...]:
    """Return three points around each selected controller boundary."""
    probes: list[BoundaryProbe] = []

    def add_single(
        prefix: str,
        dimension: str,
        values: tuple[float, ...],
        unit: str,
        step_factory: Callable[[float, int], ScenarioStep],
    ) -> None:
        for index, value in enumerate(values, start=1):
            probes.append(
                BoundaryProbe(
                    probe_id=f"EXP-{prefix}-{index:03d}",
                    dimension=dimension,
                    value=value,
                    unit=unit,
                    steps=(step_factory(value, index),),
                )
            )

    add_single(
        "SPD",
        "vehicle_speed_limit",
        (259.9, 260.0, 260.1),
        "km/h",
        lambda value, index: {
            "sequence": index,
            "reception_timestamp_ms": index * 10,
            "signals": {"vehicle_speed_kph": value},
        },
    )
    add_single(
        "THR",
        "throttle_disagreement_limit",
        (4.5, 5.0, 5.5),
        "percentage points",
        lambda value, index: {
            "sequence": 10 + index,
            "reception_timestamp_ms": 100 + index * 10,
            "signals": {
                "throttle_primary_pct": 20.0,
                "throttle_redundant_pct": 20.0 + value,
            },
        },
    )
    add_single(
        "AGE",
        "input_age_limit",
        (99.0, 100.0, 101.0),
        "ms",
        lambda value, index: {
            "sequence": 20 + index,
            "reception_timestamp_ms": 200,
            "now_ms": 200 + int(value),
        },
    )
    add_single(
        "WDG",
        "execution_budget_limit",
        (4999.0, 5000.0, 5001.0),
        "us",
        lambda value, index: {
            "sequence": 30 + index,
            "reception_timestamp_ms": 300 + index * 10,
            "execution_time_us": int(value),
        },
    )

    for index, value in enumerate((0.9, 1.0, 1.1), start=1):
        probes.append(
            BoundaryProbe(
                probe_id=f"EXP-DIR-{index:03d}",
                dimension="direction_change_speed_limit",
                value=value,
                unit="km/h",
                steps=(
                    {
                        "sequence": 40 + index * 2,
                        "reception_timestamp_ms": 400 + index * 20,
                        "signals": {
                            "vehicle_speed_kph": value,
                            "direction_request": "DRIVE",
                        },
                    },
                    {
                        "sequence": 41 + index * 2,
                        "reception_timestamp_ms": 410 + index * 20,
                        "signals": {
                            "vehicle_speed_kph": value,
                            "direction_request": "REVERSE",
                        },
                    },
                ),
            )
        )
    return tuple(probes)


def _write_generated_catalog(probes: tuple[BoundaryProbe, ...], path: Path) -> None:
    scenarios: list[dict[str, object]] = []
    for probe in probes:
        statuses = [
            status for _step in probe.steps for status in ("WAITING_FOR_PAIR", "FRAME_READY")
        ]
        scenarios.append(
            {
                "id": probe.probe_id,
                "title": f"Observe {probe.dimension} at {probe.value:g} {probe.unit}",
                "requirements": ["SIL-REQ-006", "SIL-REQ-007"],
                "steps": list(probe.steps),
                "expected": {"statuses": statuses, "output_count": len(probe.steps)},
            }
        )
    path.write_text(
        json.dumps({"schema_version": 1, "scenarios": scenarios}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _invariant_failures(outcome: ScenarioOutcome) -> tuple[str, ...]:
    failures = list(outcome.failures)
    if outcome.final_mode == "SAFE_STATE":
        expected = {
            "fault": outcome.final_fault not in (None, "NONE"),
            "gear": outcome.final_gear == "NEUTRAL",
            "torque_limit_pct": outcome.final_torque_limit_pct == 0,
            "shift_inhibited": outcome.final_shift_inhibited is True,
        }
    elif outcome.final_mode == "NORMAL":
        expected = {
            "fault": outcome.final_fault == "NONE",
            "torque_limit_pct": outcome.final_torque_limit_pct == 100,
            "shift_inhibited": outcome.final_shift_inhibited is False,
        }
    else:
        return (*failures, f"unexpected final mode: {outcome.final_mode!r}")
    failures.extend(name for name, passed in expected.items() if not passed)
    return tuple(failures)


def run_boundary_campaign(
    adapter: DutAdapter,
    output_dir: Path,
    *,
    codec: CanCodec | None = None,
) -> CampaignResult:
    """Run each probe twice and write deterministic JSON and Markdown quality status."""
    output_dir.mkdir(parents=True, exist_ok=True)
    probes = boundary_probes()
    catalog_path = output_dir / "generated-probe-catalog.json"
    _write_generated_catalog(probes, catalog_path)
    observations: list[BoundaryObservation] = []

    with ScenarioHarness(
        adapter,
        artifact_root=output_dir / "evidence",
        codec=codec,
        catalog_path=catalog_path,
    ) as harness:
        for probe in probes:
            first = harness.execute(probe.probe_id)
            second = harness.execute(probe.probe_id)
            deterministic = first.deterministic_trace_hash == second.deterministic_trace_hash
            failures = list(_invariant_failures(first))
            if not deterministic:
                failures.append("repeated execution produced a different trace hash")
            observations.append(
                BoundaryObservation(
                    probe_id=probe.probe_id,
                    dimension=probe.dimension,
                    value=probe.value,
                    unit=probe.unit,
                    mode=first.final_mode,
                    fault=first.final_fault,
                    gear=first.final_gear,
                    deterministic=deterministic,
                    invariant_failures=tuple(failures),
                    trace_sha256=first.deterministic_trace_hash,
                )
            )

    anomaly_count = sum(bool(item.invariant_failures) for item in observations)
    status = "PASS" if anomaly_count == 0 else "ATTENTION"
    json_report = output_dir / "quality-status.json"
    markdown_report = output_dir / "quality-status.md"
    payload = {
        "schema_version": 1,
        "status": status,
        "probe_count": len(probes),
        "execution_count": len(probes) * 2,
        "anomaly_count": anomaly_count,
        "observations": [asdict(item) for item in observations],
    }
    json_report.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    rows = [
        "# Exploratory Boundary Campaign Quality Status",
        "",
        f"Status: **{status}**",
        "",
        (
            f"Executed {len(probes)} boundary probes twice "
            f"({len(probes) * 2} executions) against the selected DUT adapter."
        ),
        "",
        "| Probe | Dimension | Value | Mode | Fault | Deterministic | Invariant findings |",
        "|---|---|---:|---|---|---|---|",
    ]
    for item in observations:
        findings = "; ".join(item.invariant_failures) or "none"
        rows.append(
            "| "
            f"{item.probe_id} | {item.dimension} | {item.value:g} {item.unit} | "
            f"{item.mode} | {item.fault} | {'yes' if item.deterministic else 'no'} | "
            f"{findings} |"
        )
    markdown_report.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    return CampaignResult(
        status=status,
        probe_count=len(probes),
        execution_count=len(probes) * 2,
        anomaly_count=anomaly_count,
        observations=tuple(observations),
        json_report=json_report,
        markdown_report=markdown_report,
    )
