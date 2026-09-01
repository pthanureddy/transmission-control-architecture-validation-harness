"""Deterministic virtual-CAN scenario execution and result oracles."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

import can
from cantools.database.errors import DecodeError

from tca_sil.bridge import DutAdapter
from tca_sil.catalog import ScenarioSpec, ScenarioStep, load_catalog
from tca_sil.codec import CanCodec
from tca_sil.diagnostics import DiagnosticMemory
from tca_sil.evidence import EvidenceRecorder, write_manifest
from tca_sil.faults import inject_fault
from tca_sil.models import (
    DirectionRequest,
    DriverSignals,
    DutResult,
    FaultCode,
    MotionSignals,
)


@dataclass(frozen=True, slots=True)
class ScenarioOutcome:
    scenario_id: str
    title: str
    requirements: list[str]
    passed: bool
    failures: list[str]
    observed_statuses: list[str]
    output_count: int
    final_mode: str | None
    final_fault: str | None
    final_gear: str | None
    final_torque_limit_pct: int | None
    final_shift_inhibited: bool | None
    diagnostic_records: list[dict[str, object]]
    first_fault: str | None
    deterministic_trace_hash: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ScenarioHarness:
    """Run catalog scenarios through python-can VirtualBus and the compiled DUT adapter."""

    def __init__(
        self,
        adapter: DutAdapter,
        *,
        artifact_root: Path,
        codec: CanCodec | None = None,
        catalog_path: Path | None = None,
    ) -> None:
        self.adapter = adapter
        self.codec = codec or CanCodec()
        self.catalog = load_catalog(catalog_path)
        self.artifact_root = artifact_root
        channel = f"tca-sil-{uuid.uuid4()}"
        self._stimulus_bus = can.Bus(
            interface="virtual", channel=f"{channel}-input", receive_own_messages=False
        )
        self._dut_input_bus = can.Bus(
            interface="virtual",
            channel=f"{channel}-input",
            receive_own_messages=False,
            preserve_timestamps=True,
        )
        self._dut_output_bus = can.Bus(
            interface="virtual", channel=f"{channel}-output", receive_own_messages=False
        )
        self._observer_bus = can.Bus(
            interface="virtual",
            channel=f"{channel}-output",
            receive_own_messages=False,
            preserve_timestamps=True,
        )
        self._manifest_entries: dict[str, dict[str, object]] = {}
        self._closed = False

    def execute(self, scenario_id: str) -> ScenarioOutcome:
        if self._closed:
            raise RuntimeError("Scenario harness is closed")
        try:
            spec = self.catalog[scenario_id]
        except KeyError as error:
            raise KeyError(f"Unknown scenario: {scenario_id}") from error
        self.adapter.reset()
        diagnostics = DiagnosticMemory()
        recorder = EvidenceRecorder(scenario_id)
        observed: list[DutResult] = []

        for step_index, step in enumerate(spec["steps"], start=1):
            self._execute_step(step, step_index, recorder, observed, diagnostics)

        outcome = self._evaluate(spec, observed, diagnostics, recorder)
        entry = recorder.write(self.artifact_root, outcome)
        self._manifest_entries[scenario_id] = entry
        write_manifest(self.artifact_root, list(self._manifest_entries.values()))
        return outcome

    def _execute_step(
        self,
        step: ScenarioStep,
        step_index: int,
        recorder: EvidenceRecorder,
        observed: list[DutResult],
        diagnostics: DiagnosticMemory,
    ) -> None:
        sequence = int(step.get("sequence", step_index))
        reception_ms = int(step.get("reception_timestamp_ms", step_index * 10))
        now_ms = int(step.get("now_ms", reception_ms))
        execution_us = int(step.get("execution_time_us", 800))
        signals = step.get("signals", {})
        motion = MotionSignals(
            vehicle_speed_kph=float(signals.get("vehicle_speed_kph", 8.0)),
            input_shaft_rpm=float(signals.get("input_shaft_rpm", 1500.0)),
            output_shaft_rpm=float(signals.get("output_shaft_rpm", 400.0)),
            sequence=sequence,
        )
        direction_name = str(signals.get("direction_request", "DRIVE")).upper()
        driver = DriverSignals(
            throttle_primary_pct=float(signals.get("throttle_primary_pct", 20.0)),
            throttle_redundant_pct=float(signals.get("throttle_redundant_pct", 20.0)),
            direction_request=DirectionRequest[direction_name],
            brake_applied=bool(signals.get("brake_applied", False)),
            sequence=int(step.get("driver_sequence", sequence)),
        )
        frames = {
            "motion": self.codec.encode_motion(motion, timestamp_ms=reception_ms),
            "driver": self.codec.encode_driver(driver, timestamp_ms=reception_ms),
        }
        fault = str(step.get("fault", "none"))
        target = str(step.get("fault_target", ""))
        order = step.get("order", ["motion", "driver"])
        for source in order:
            if source not in frames:
                raise ValueError(f"Unsupported frame source {source!r}")
            message = frames[source]
            selected_fault = fault if source == target else "none"
            mutated = inject_fault(message, selected_fault, self.codec)
            if mutated is None:
                recorder.add(
                    simulated_time_ms=reception_ms,
                    event_type="frame_dropped",
                    source=source,
                    arbitration_id=message.arbitration_id,
                    dlc=message.dlc,
                    data=bytes(message.data),
                    decoded=self._safe_decode(message),
                    note=f"injected_fault={selected_fault}",
                )
                continue
            result = self._transmit(
                mutated,
                source=source,
                reception_ms=reception_ms,
                now_ms=now_ms,
                execution_us=execution_us,
                injected_fault=selected_fault,
                recorder=recorder,
            )
            observed.append(result)
            diagnostics.observe(result, simulated_time_ms=now_ms)

    def _transmit(
        self,
        message: can.Message,
        *,
        source: str,
        reception_ms: int,
        now_ms: int,
        execution_us: int,
        injected_fault: str,
        recorder: EvidenceRecorder,
    ) -> DutResult:
        self._stimulus_bus.send(message)
        received = self._dut_input_bus.recv(timeout=0.5)
        if received is None:
            raise TimeoutError("Virtual input frame was not delivered to the DUT adapter")
        recorder.add(
            simulated_time_ms=reception_ms,
            event_type="can_rx",
            source=source,
            arbitration_id=received.arbitration_id,
            dlc=received.dlc,
            data=bytes(received.data),
            decoded=self._safe_decode(received),
            note=(f"injected_fault={injected_fault}" if injected_fault != "none" else None),
        )
        result = self.adapter.ingest(
            received,
            reception_timestamp_ms=reception_ms,
            now_ms=now_ms,
            execution_time_us=execution_us,
        )
        recorder.add(
            simulated_time_ms=now_ms,
            event_type="ingest_result",
            source="compiled_dut",
            ingest_status=result.ingest_status.name,
            fault_code=result.fault_code.name if result.fault_code is not None else None,
        )
        if result.has_output:
            output = can.Message(
                arbitration_id=result.output_can_id,
                data=result.output_data,
                dlc=result.output_dlc,
                is_extended_id=False,
                timestamp=now_ms / 1000.0,
                check=True,
            )
            self._dut_output_bus.send(output)
            observed = self._observer_bus.recv(timeout=0.5)
            if observed is None:
                raise TimeoutError("Virtual output frame was not delivered to the observer")
            recorder.add(
                simulated_time_ms=now_ms,
                event_type="can_tx",
                source="compiled_dut",
                arbitration_id=observed.arbitration_id,
                dlc=observed.dlc,
                data=bytes(observed.data),
                decoded=self._safe_decode(observed),
                fault_code=result.fault_code.name if result.fault_code is not None else None,
            )
        return result

    def _safe_decode(self, message: can.Message) -> dict[str, object] | None:
        try:
            return self.codec.decode(message)
        except (KeyError, ValueError, DecodeError):
            return None

    @staticmethod
    def _evaluate(
        spec: ScenarioSpec,
        observed: list[DutResult],
        diagnostics: DiagnosticMemory,
        recorder: EvidenceRecorder,
    ) -> ScenarioOutcome:
        expected = spec["expected"]
        failures: list[str] = []
        statuses = [item.ingest_status.name for item in observed]
        outputs = [item for item in observed if item.has_output]
        final = outputs[-1] if outputs else None
        ScenarioHarness._compare("statuses", statuses, expected.get("statuses"), failures)
        ScenarioHarness._compare(
            "output_count", len(outputs), expected.get("output_count"), failures
        )
        fields: list[tuple[str, object | None]] = [
            (
                "mode",
                final.operating_mode.name if final and final.operating_mode is not None else None,
            ),
            ("fault", final.fault_code.name if final and final.fault_code is not None else None),
            (
                "gear",
                final.selected_gear.name if final and final.selected_gear is not None else None,
            ),
            ("torque_limit_pct", final.torque_limit_pct if final else None),
            ("shift_inhibited", final.shift_inhibited if final else None),
        ]
        for field, actual in fields:
            ScenarioHarness._compare(field, actual, expected.get(field), failures)
        diagnostic_records = diagnostics.read()
        expected_dtc = expected.get("active_dtc")
        if expected_dtc is not None:
            active = [item["code"] for item in diagnostic_records if item["active"]]
            ScenarioHarness._compare("active_dtc", active, [expected_dtc], failures)

        first_fault = ScenarioHarness._first_fault(recorder)
        return ScenarioOutcome(
            scenario_id=spec["id"],
            title=spec["title"],
            requirements=spec["requirements"],
            passed=not failures,
            failures=failures,
            observed_statuses=statuses,
            output_count=len(outputs),
            final_mode=(
                final.operating_mode.name if final and final.operating_mode is not None else None
            ),
            final_fault=final.fault_code.name if final and final.fault_code is not None else None,
            final_gear=(
                final.selected_gear.name if final and final.selected_gear is not None else None
            ),
            final_torque_limit_pct=final.torque_limit_pct if final else None,
            final_shift_inhibited=final.shift_inhibited if final else None,
            diagnostic_records=diagnostic_records,
            first_fault=first_fault,
            deterministic_trace_hash=recorder.deterministic_hash(),
        )

    @staticmethod
    def _compare(name: str, actual: object, expected: object | None, failures: list[str]) -> None:
        if expected is not None and actual != expected:
            failures.append(f"{name}: expected {expected!r}, observed {actual!r}")

    @staticmethod
    def _first_fault(recorder: EvidenceRecorder) -> str | None:
        normal_statuses = {"WAITING_FOR_PAIR", "FRAME_READY"}
        for event in recorder.events:
            if event.ingest_status and event.ingest_status not in normal_statuses:
                return f"ingest:{event.ingest_status}@{event.simulated_time_ms}ms"
            if event.fault_code and event.fault_code != FaultCode.NONE.name:
                return f"dut:{event.fault_code}@{event.simulated_time_ms}ms"
        return None

    def close(self) -> None:
        if self._closed:
            return
        write_manifest(self.artifact_root, list(self._manifest_entries.values()))
        self._stimulus_bus.shutdown()
        self._dut_input_bus.shutdown()
        self._dut_output_bus.shutdown()
        self._observer_bus.shutdown()
        self.adapter.close()
        self._closed = True

    def __enter__(self) -> ScenarioHarness:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
