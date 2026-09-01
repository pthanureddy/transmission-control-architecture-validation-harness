from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tca_sil.diagnostics import DiagnosticMemory
from tca_sil.evidence import EvidenceRecorder, canonical_json, sha256_text, write_manifest
from tca_sil.harness import ScenarioOutcome
from tca_sil.models import DutResult, FaultCode, Gear, IngestStatus, OperatingMode


def fault_result(fault: FaultCode = FaultCode.SENSOR_DISAGREEMENT) -> DutResult:
    return DutResult(
        ingest_status=IngestStatus.FRAME_READY,
        has_output=True,
        output_sequence=1,
        output_can_id=0x280,
        output_dlc=8,
        output_data=b"12345678",
        selected_gear=Gear.NEUTRAL,
        operating_mode=OperatingMode.SAFE_STATE,
        fault_code=fault,
        torque_limit_pct=0,
        shift_inhibited=True,
    )


def test_diagnostic_memory_ignores_non_output() -> None:
    memory = DiagnosticMemory()
    memory.observe(DutResult(IngestStatus.WAITING_FOR_PAIR, False), simulated_time_ms=10)
    assert memory.read() == []


def test_diagnostic_memory_captures_first_fault_snapshot() -> None:
    memory = DiagnosticMemory()
    memory.observe(fault_result(), simulated_time_ms=10)
    record = memory.read()[0]
    assert record["code"] == "TCA-SENSOR-DISAGREEMENT"
    assert record["active"] is True
    assert record["first_seen_ms"] == 10
    assert record["snapshot"]["torque_limit_pct"] == 0  # type: ignore[index]


def test_diagnostic_snapshot_preserves_zero_valued_enums() -> None:
    memory = DiagnosticMemory()
    result = DutResult(
        ingest_status=IngestStatus.FRAME_READY,
        has_output=True,
        selected_gear=Gear.PARK,
        operating_mode=OperatingMode.INITIALIZING,
        fault_code=FaultCode.INPUT_RANGE,
    )
    memory.observe(result, simulated_time_ms=10)
    snapshot = memory.read()[0]["snapshot"]
    assert snapshot["gear"] == "PARK"  # type: ignore[index]
    assert snapshot["mode"] == "INITIALIZING"  # type: ignore[index]


def test_diagnostic_memory_updates_occurrence() -> None:
    memory = DiagnosticMemory()
    memory.observe(fault_result(), simulated_time_ms=10)
    memory.observe(fault_result(), simulated_time_ms=20)
    record = memory.read()[0]
    assert record["occurrence_count"] == 2
    assert record["last_seen_ms"] == 20


def test_active_dtc_cannot_be_cleared() -> None:
    memory = DiagnosticMemory()
    memory.observe(fault_result(), simulated_time_ms=10)
    assert memory.clear() is False
    assert len(memory.read()) == 1


def test_stored_dtc_can_be_cleared_after_ignition_cycle() -> None:
    memory = DiagnosticMemory()
    memory.observe(fault_result(), simulated_time_ms=10)
    memory.ignition_cycle()
    assert memory.read()[0]["active"] is False
    assert memory.clear() is True
    assert memory.read() == []


def sample_outcome(trace_hash: str) -> ScenarioOutcome:
    return ScenarioOutcome(
        scenario_id="SAMPLE",
        title="sample",
        requirements=["REQ-1"],
        passed=True,
        failures=[],
        observed_statuses=["FRAME_READY"],
        output_count=1,
        final_mode="NORMAL",
        final_fault="NONE",
        final_gear="FIRST",
        final_torque_limit_pct=100,
        final_shift_inhibited=False,
        diagnostic_records=[],
        first_fault=None,
        deterministic_trace_hash=trace_hash,
    )


def test_canonical_json_and_hash_are_stable() -> None:
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    assert sha256_text("abc") == hashlib.sha256(b"abc").hexdigest()


def test_evidence_recorder_writes_trace_and_summary(tmp_path: Path) -> None:
    recorder = EvidenceRecorder("SAMPLE")
    recorder.add(
        simulated_time_ms=10,
        event_type="can_rx",
        source="motion",
        arbitration_id=0x180,
        dlc=8,
        data=b"12345678",
    )
    outcome = sample_outcome(recorder.deterministic_hash())
    entry = recorder.write(tmp_path, outcome)
    assert (tmp_path / entry["trace"]).is_file()  # type: ignore[operator]
    summary = json.loads((tmp_path / entry["summary"]).read_text(encoding="utf-8"))  # type: ignore[operator]
    assert summary["passed"] is True
    assert len(summary["trace_sha256"]) == 64


def test_manifest_is_sorted_and_counts_passes(tmp_path: Path) -> None:
    path = write_manifest(
        tmp_path,
        [
            {"scenario_id": "B", "passed": False},
            {"scenario_id": "A", "passed": True},
        ],
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert [entry["scenario_id"] for entry in manifest["entries"]] == ["A", "B"]
    assert manifest["passed_count"] == 1
