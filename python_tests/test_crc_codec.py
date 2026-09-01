from __future__ import annotations

import pytest
from tca_sil.codec import DRIVER_REQUEST_CAN_ID, MOTION_CAN_ID, CanCodec
from tca_sil.crc import can_crc, crc8_sae_j1850, finalize_can_payload
from tca_sil.models import DirectionRequest, DriverSignals, MotionSignals


def test_crc_empty_payload_matches_c_implementation() -> None:
    assert crc8_sae_j1850(b"") == 0


def test_crc_known_can_motion_vector() -> None:
    payload = bytes.fromhex("5000DC0590010100")
    assert can_crc(MOTION_CAN_ID, 8, payload) == 0x8B


def test_can_crc_requires_seven_payload_bytes() -> None:
    with pytest.raises(ValueError, match="seven bytes"):
        can_crc(MOTION_CAN_ID, 8, b"short")


def test_finalize_requires_classical_eight_byte_payload() -> None:
    with pytest.raises(ValueError, match="exactly eight"):
        finalize_can_payload(MOTION_CAN_ID, b"1234567")


def test_motion_codec_matches_cpp_signal_layout() -> None:
    codec = CanCodec()
    message = codec.encode_motion(MotionSignals(8.0, 1500.0, 400.0, 1), timestamp_ms=10)
    assert message.arbitration_id == MOTION_CAN_ID
    assert bytes(message.data) == bytes.fromhex("5000DC059001018B")
    assert codec.decode(message)["VehicleSpeedKph"] == 8.0


def test_driver_codec_matches_cpp_signal_layout() -> None:
    codec = CanCodec()
    signals = DriverSignals(20.0, 20.0, DirectionRequest.DRIVE, False, 1)
    message = codec.encode_driver(signals, timestamp_ms=10)
    assert message.arbitration_id == DRIVER_REQUEST_CAN_ID
    assert bytes(message.data) == bytes.fromhex("282802000000018D")
    assert codec.decode(message)["DirectionRequest"] == 2


def test_recalculate_crc_repairs_mutated_payload() -> None:
    codec = CanCodec()
    message = codec.encode_motion(MotionSignals(8.0, 1500.0, 400.0, 1), timestamp_ms=10)
    data = bytearray(message.data)
    data[0] ^= 1
    message.data = data
    repaired = codec.recalculate_crc(message)
    assert repaired.data[7] == can_crc(repaired.arbitration_id, repaired.dlc, repaired.data)
