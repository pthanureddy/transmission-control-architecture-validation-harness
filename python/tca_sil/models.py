"""Shared types whose numeric values mirror the compiled C/C++ DUT."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class DirectionRequest(IntEnum):
    PARK = 0
    NEUTRAL = 1
    DRIVE = 2
    REVERSE = 3


class IngestStatus(IntEnum):
    WAITING_FOR_PAIR = 0
    FRAME_READY = 1
    UNKNOWN_IDENTIFIER = 2
    INVALID_LENGTH = 3
    INVALID_CRC = 4
    INVALID_SIGNAL = 5
    SEQUENCE_MISMATCH = 6


class Gear(IntEnum):
    PARK = 0
    NEUTRAL = 1
    REVERSE = 2
    FIRST = 3
    SECOND = 4
    THIRD = 5
    FOURTH = 6
    FIFTH = 7
    SIXTH = 8


class OperatingMode(IntEnum):
    INITIALIZING = 0
    NORMAL = 1
    SAFE_STATE = 2


class FaultCode(IntEnum):
    NONE = 0
    INPUT_RANGE = 1
    SENSOR_DISAGREEMENT = 2
    STALE_INPUT = 3
    ILLEGAL_DIRECTION_CHANGE = 4
    WATCHDOG_OVERRUN = 5


@dataclass(frozen=True, slots=True)
class MotionSignals:
    vehicle_speed_kph: float
    input_shaft_rpm: float
    output_shaft_rpm: float
    sequence: int


@dataclass(frozen=True, slots=True)
class DriverSignals:
    throttle_primary_pct: float
    throttle_redundant_pct: float
    direction_request: DirectionRequest
    brake_applied: bool
    sequence: int


@dataclass(frozen=True, slots=True)
class DutResult:
    ingest_status: IngestStatus
    has_output: bool
    output_sequence: int = 0
    output_can_id: int = 0
    output_dlc: int = 0
    output_data: bytes = b""
    selected_gear: Gear | None = None
    operating_mode: OperatingMode | None = None
    fault_code: FaultCode | None = None
    torque_limit_pct: int = 0
    shift_inhibited: bool = True


@dataclass(frozen=True, slots=True)
class TraceEvent:
    index: int
    scenario_id: str
    simulated_time_ms: int
    event_type: str
    source: str
    arbitration_id: str | None = None
    dlc: int | None = None
    data_hex: str | None = None
    decoded: dict[str, object] | None = None
    ingest_status: str | None = None
    fault_code: str | None = None
    note: str | None = None
