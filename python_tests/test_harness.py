from __future__ import annotations

import json
from pathlib import Path

import pytest
from tca_sil.codec import CanCodec
from tca_sil.harness import ScenarioHarness

from python_tests.support import ReferenceAdapter

SCENARIOS = [
    "SIL-NOM-001",
    "SIL-ORD-001",
    "SIL-CRC-001",
    "SIL-DLC-001",
    "SIL-ID-001",
    "SIL-SIG-001",
    "SIL-SEQ-001",
    "SIL-DROP-001",
    "SIL-PLS-001",
    "SIL-RNG-001",
    "SIL-AGE-001",
    "SIL-DIR-001",
    "SIL-WDG-001",
    "SIL-LAT-001",
]


@pytest.mark.parametrize("scenario_id", SCENARIOS)
def test_scenario_oracle_and_virtual_bus_plumbing(scenario_id: str, tmp_path: Path) -> None:
    """Exercise automation logic with a test-only reference adapter, not the DUT."""
    codec = CanCodec()
    with ScenarioHarness(
        ReferenceAdapter(codec), artifact_root=tmp_path / "evidence", codec=codec
    ) as harness:
        outcome = harness.execute(scenario_id)
    assert outcome.passed, outcome.failures
    assert (tmp_path / "evidence" / scenario_id / "trace.jsonl").is_file()


def test_repeated_scenario_has_same_trace_hash(tmp_path: Path) -> None:
    codec = CanCodec()
    with ScenarioHarness(
        ReferenceAdapter(codec), artifact_root=tmp_path / "evidence", codec=codec
    ) as harness:
        first = harness.execute("SIL-NOM-001")
        second = harness.execute("SIL-NOM-001")
    assert first.deterministic_trace_hash == second.deterministic_trace_hash


def test_unknown_scenario_is_rejected(tmp_path: Path) -> None:
    codec = CanCodec()
    with (
        ScenarioHarness(
            ReferenceAdapter(codec), artifact_root=tmp_path / "evidence", codec=codec
        ) as harness,
        pytest.raises(KeyError, match="Unknown scenario"),
    ):
        harness.execute("NOT-REAL")


def test_closed_harness_rejects_execution(tmp_path: Path) -> None:
    codec = CanCodec()
    harness = ScenarioHarness(
        ReferenceAdapter(codec), artifact_root=tmp_path / "evidence", codec=codec
    )
    harness.close()
    harness.close()
    with pytest.raises(RuntimeError, match="closed"):
        harness.execute("SIL-NOM-001")


def test_failure_oracle_records_mismatch(tmp_path: Path) -> None:
    catalog = json.loads(
        (Path(__file__).resolve().parents[1] / "scenarios" / "catalog.json").read_text(
            encoding="utf-8"
        )
    )
    catalog["scenarios"] = [catalog["scenarios"][0]]
    catalog["scenarios"][0]["expected"]["gear"] = "SIXTH"
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    codec = CanCodec()
    with ScenarioHarness(
        ReferenceAdapter(codec),
        artifact_root=tmp_path / "evidence",
        codec=codec,
        catalog_path=catalog_path,
    ) as harness:
        outcome = harness.execute("SIL-NOM-001")
    assert outcome.passed is False
    assert "gear" in outcome.failures[0]


def test_first_fault_is_correlated_for_crc_rejection(tmp_path: Path) -> None:
    codec = CanCodec()
    with ScenarioHarness(
        ReferenceAdapter(codec), artifact_root=tmp_path / "evidence", codec=codec
    ) as harness:
        outcome = harness.execute("SIL-CRC-001")
    assert outcome.first_fault == "ingest:INVALID_CRC@30ms"


def test_first_fault_is_correlated_for_controller_fault(tmp_path: Path) -> None:
    codec = CanCodec()
    with ScenarioHarness(
        ReferenceAdapter(codec), artifact_root=tmp_path / "evidence", codec=codec
    ) as harness:
        outcome = harness.execute("SIL-PLS-001")
    assert outcome.first_fault == "dut:SENSOR_DISAGREEMENT@90ms"
