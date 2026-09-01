"""Deterministic frame mutations used by negative-path scenarios."""

from __future__ import annotations

import can

from tca_sil.codec import CanCodec


def clone_message(
    message: can.Message,
    *,
    arbitration_id: int | None = None,
    dlc: int | None = None,
    data: bytes | None = None,
) -> can.Message:
    return can.Message(
        arbitration_id=message.arbitration_id if arbitration_id is None else arbitration_id,
        data=bytes(message.data) if data is None else data,
        dlc=message.dlc if dlc is None else dlc,
        is_extended_id=False,
        timestamp=message.timestamp,
        check=False,
    )


def inject_fault(message: can.Message, fault: str, codec: CanCodec) -> can.Message | None:
    if fault == "none":
        return message
    if fault == "drop":
        return None
    if fault == "corrupt_crc":
        data = bytearray(message.data)
        data[0] ^= 0x01
        return clone_message(message, data=bytes(data))
    if fault == "wrong_dlc":
        return clone_message(message, dlc=7)
    if fault == "unknown_identifier":
        return clone_message(message, arbitration_id=0x555)
    if fault == "invalid_direction":
        data = bytearray(message.data)
        data[2] = 7
        mutated = clone_message(message, data=bytes(data))
        return codec.recalculate_crc(mutated)
    raise ValueError(f"Unsupported fault type: {fault}")
