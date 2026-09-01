"""Small diagnostic-event memory for fault-tracing tests.

This is a repository-defined service model. It is deliberately not described
as an ISO 14229 implementation or as a production diagnostic stack.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from tca_sil.models import DutResult, FaultCode

PROJECT_DTCS = {
    FaultCode.INPUT_RANGE: "TCA-INPUT-RANGE",
    FaultCode.SENSOR_DISAGREEMENT: "TCA-SENSOR-DISAGREEMENT",
    FaultCode.STALE_INPUT: "TCA-STALE-INPUT",
    FaultCode.ILLEGAL_DIRECTION_CHANGE: "TCA-DIRECTION-CHANGE",
    FaultCode.WATCHDOG_OVERRUN: "TCA-WATCHDOG-OVERRUN",
}


@dataclass(slots=True)
class DtcRecord:
    code: str
    source_fault: str
    active: bool
    stored: bool
    first_seen_ms: int
    last_seen_ms: int
    occurrence_count: int
    snapshot: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class DiagnosticMemory:
    """Track active/stored project DTCs and guarded clear behavior."""

    def __init__(self) -> None:
        self._records: dict[str, DtcRecord] = {}

    def observe(self, result: DutResult, *, simulated_time_ms: int) -> None:
        fault = result.fault_code
        if not result.has_output or fault in (None, FaultCode.NONE):
            return
        assert fault is not None
        code = PROJECT_DTCS[fault]
        record = self._records.get(code)
        snapshot: dict[str, object] = {
            "output_sequence": result.output_sequence,
            "mode": result.operating_mode.name if result.operating_mode is not None else None,
            "gear": result.selected_gear.name if result.selected_gear is not None else None,
            "torque_limit_pct": result.torque_limit_pct,
            "shift_inhibited": result.shift_inhibited,
        }
        if record is None:
            self._records[code] = DtcRecord(
                code=code,
                source_fault=fault.name,
                active=True,
                stored=True,
                first_seen_ms=simulated_time_ms,
                last_seen_ms=simulated_time_ms,
                occurrence_count=1,
                snapshot=snapshot,
            )
            return
        record.active = True
        record.stored = True
        record.last_seen_ms = simulated_time_ms
        record.occurrence_count += 1
        record.snapshot = snapshot

    def ignition_cycle(self) -> None:
        for record in self._records.values():
            record.active = False

    def read(self) -> list[dict[str, object]]:
        return [self._records[key].to_dict() for key in sorted(self._records)]

    def clear(self) -> bool:
        if any(record.active for record in self._records.values()):
            return False
        self._records.clear()
        return True
