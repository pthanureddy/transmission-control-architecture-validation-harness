"""Test-only reference adapter for exercising harness plumbing without a compiler.

It is intentionally not used by Robot Framework or verification evidence. Hosted
acceptance tests always load the compiled C/C++ shared library.
"""

from __future__ import annotations

import can
from tca_sil.bridge import DutAdapter
from tca_sil.codec import CONTROL_OUTPUT_CAN_ID, DRIVER_REQUEST_CAN_ID, MOTION_CAN_ID, CanCodec
from tca_sil.crc import can_crc, finalize_can_payload
from tca_sil.models import DutResult, FaultCode, Gear, IngestStatus, OperatingMode


class ReferenceAdapter(DutAdapter):
    def __init__(self, codec: CanCodec | None = None) -> None:
        self.codec = codec or CanCodec()
        self.closed = False
        self.reset()

    def reset(self) -> None:
        self.motion: dict[str, object] | None = None
        self.driver: dict[str, object] | None = None
        self.current_direction = 0
        self.latched_fault = FaultCode.NONE
        self.output_sequence = 0

    def close(self) -> None:
        self.closed = True

    def ingest(
        self,
        message: can.Message,
        *,
        reception_timestamp_ms: int,
        now_ms: int,
        execution_time_us: int,
    ) -> DutResult:
        if message.arbitration_id not in (MOTION_CAN_ID, DRIVER_REQUEST_CAN_ID):
            return DutResult(IngestStatus.UNKNOWN_IDENTIFIER, False)
        if message.dlc != 8:
            return DutResult(IngestStatus.INVALID_LENGTH, False)
        if bytes(message.data)[7] != can_crc(
            message.arbitration_id, message.dlc, bytes(message.data)
        ):
            return DutResult(IngestStatus.INVALID_CRC, False)
        decoded = self.codec.decode(message)
        if message.arbitration_id == MOTION_CAN_ID:
            self.motion = decoded
        else:
            if int(decoded["DirectionRequest"]) > 3:
                return DutResult(IngestStatus.INVALID_SIGNAL, False)
            self.driver = decoded
        if self.motion is None or self.driver is None:
            return DutResult(IngestStatus.WAITING_FOR_PAIR, False)
        if int(self.motion["RollingCounter"]) != int(self.driver["RollingCounter"]):
            return DutResult(IngestStatus.SEQUENCE_MISMATCH, False)
        motion, driver = self.motion, self.driver
        self.motion = None
        self.driver = None
        return self._step(motion, driver, reception_timestamp_ms, now_ms, execution_time_us)

    def _step(
        self,
        motion: dict[str, object],
        driver: dict[str, object],
        reception_ms: int,
        now_ms: int,
        execution_us: int,
    ) -> DutResult:
        speed = float(motion["VehicleSpeedKph"])
        input_rpm = float(motion["InputShaftRpm"])
        output_rpm = float(motion["OutputShaftRpm"])
        primary = float(driver["ThrottlePrimaryPct"])
        redundant = float(driver["ThrottleRedundantPct"])
        direction = int(driver["DirectionRequest"])
        fault = FaultCode.NONE
        if (
            speed > 260
            or input_rpm > 12000
            or output_rpm > 12000
            or primary > 100
            or redundant > 100
        ):
            fault = FaultCode.INPUT_RANGE
        elif abs(primary - redundant) > 5:
            fault = FaultCode.SENSOR_DISAGREEMENT
        elif now_ms - reception_ms > 100:
            fault = FaultCode.STALE_INPUT
        elif (
            direction != self.current_direction
            and speed > 1
            and (direction in (0, 3) or (self.current_direction == 3 and direction == 2))
        ):
            fault = FaultCode.ILLEGAL_DIRECTION_CHANGE
        elif execution_us > 5000:
            fault = FaultCode.WATCHDOG_OVERRUN

        if fault != FaultCode.NONE and self.latched_fault == FaultCode.NONE:
            self.latched_fault = fault
        self.output_sequence += 1
        if self.latched_fault != FaultCode.NONE:
            mode = OperatingMode.SAFE_STATE
            gear = Gear.NEUTRAL
            torque = 0
            inhibited = True
            self.current_direction = 1
        else:
            mode = OperatingMode.NORMAL
            gear = self._gear(direction, speed, primary)
            torque = 100
            inhibited = False
            self.current_direction = direction
        payload = bytearray(8)
        payload[0] = int(gear)
        payload[1] = int(mode)
        payload[2] = int(self.latched_fault)
        payload[3] = torque
        payload[4] = int(inhibited)
        payload[5] = self.output_sequence & 0xFF
        payload[6] = (self.output_sequence >> 8) & 0xFF
        output_data = finalize_can_payload(CONTROL_OUTPUT_CAN_ID, bytes(payload))
        return DutResult(
            ingest_status=IngestStatus.FRAME_READY,
            has_output=True,
            output_sequence=self.output_sequence,
            output_can_id=CONTROL_OUTPUT_CAN_ID,
            output_dlc=8,
            output_data=output_data,
            selected_gear=gear,
            operating_mode=mode,
            fault_code=self.latched_fault,
            torque_limit_pct=torque,
            shift_inhibited=inhibited,
        )

    @staticmethod
    def _gear(direction: int, speed: float, throttle: float) -> Gear:
        if direction == 0:
            return Gear.PARK
        if direction == 1:
            return Gear.NEUTRAL
        if direction == 3:
            return Gear.REVERSE
        offset = 12 if throttle >= 70 else 6 if throttle >= 35 else 0
        thresholds = (15 + offset, 30 + offset, 50 + offset, 75 + offset, 105 + offset)
        for gear, threshold in zip(
            (Gear.FIRST, Gear.SECOND, Gear.THIRD, Gear.FOURTH, Gear.FIFTH),
            thresholds,
            strict=True,
        ):
            if speed < threshold:
                return gear
        return Gear.SIXTH
