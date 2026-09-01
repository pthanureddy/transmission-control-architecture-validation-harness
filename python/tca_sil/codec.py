"""DBC-backed encoding for the repository-defined synthetic CAN frames."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import can
import cantools
from cantools.database.can import Database as CanDatabase

from tca_sil.crc import finalize_can_payload
from tca_sil.models import DriverSignals, MotionSignals

MOTION_CAN_ID = 0x180
DRIVER_REQUEST_CAN_ID = 0x181
CONTROL_OUTPUT_CAN_ID = 0x280


def default_dbc_path() -> Path:
    return Path(__file__).resolve().parents[2] / "network" / "tca_synthetic.dbc"


class CanCodec:
    """Encode/decode synthetic frames using a reviewable DBC plus the DUT CRC."""

    def __init__(self, dbc_path: Path | None = None) -> None:
        self.dbc_path = dbc_path or default_dbc_path()
        loaded = cantools.database.load_file(str(self.dbc_path), strict=True)
        if not isinstance(loaded, CanDatabase):
            raise TypeError(f"Expected a CAN database: {self.dbc_path}")
        self._database = loaded

    def encode_motion(self, signals: MotionSignals, *, timestamp_ms: int) -> can.Message:
        payload = self._database.encode_message(
            "MotionState",
            {
                "VehicleSpeedKph": signals.vehicle_speed_kph,
                "InputShaftRpm": signals.input_shaft_rpm,
                "OutputShaftRpm": signals.output_shaft_rpm,
                "RollingCounter": signals.sequence & 0xFF,
                "Crc": 0,
            },
            strict=True,
        )
        return self._message(MOTION_CAN_ID, payload, timestamp_ms)

    def encode_driver(self, signals: DriverSignals, *, timestamp_ms: int) -> can.Message:
        payload = self._database.encode_message(
            "DriverRequest",
            {
                "ThrottlePrimaryPct": signals.throttle_primary_pct,
                "ThrottleRedundantPct": signals.throttle_redundant_pct,
                "DirectionRequest": int(signals.direction_request),
                "BrakeApplied": int(signals.brake_applied),
                "RollingCounter": signals.sequence & 0xFF,
                "Crc": 0,
            },
            strict=True,
        )
        return self._message(DRIVER_REQUEST_CAN_ID, payload, timestamp_ms)

    def decode(self, message: can.Message) -> dict[str, object]:
        decoded = cast(
            dict[str, Any],
            self._database.decode_message(
                message.arbitration_id,
                bytes(message.data),
                decode_choices=False,
            ),
        )
        return {key: self._normalize(value) for key, value in decoded.items()}

    @staticmethod
    def _normalize(value: Any) -> object:
        if isinstance(value, (bool, int, float, str)):
            return value
        return str(value)

    @staticmethod
    def _message(arbitration_id: int, payload: bytes, timestamp_ms: int) -> can.Message:
        data = finalize_can_payload(arbitration_id, payload)
        return can.Message(
            arbitration_id=arbitration_id,
            data=data,
            dlc=8,
            is_extended_id=False,
            timestamp=timestamp_ms / 1000.0,
            check=True,
        )

    def recalculate_crc(self, message: can.Message) -> can.Message:
        data = finalize_can_payload(message.arbitration_id, bytes(message.data), dlc=message.dlc)
        return can.Message(
            arbitration_id=message.arbitration_id,
            data=data,
            dlc=message.dlc,
            is_extended_id=False,
            timestamp=message.timestamp,
            check=False,
        )
