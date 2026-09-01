"""CRC functions shared by the DBC codec and fault injection."""

from __future__ import annotations


def crc8_sae_j1850(data: bytes) -> int:
    """Match ``tca_crc8_sae_j1850`` in the C11 implementation."""
    crc = 0xFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1D) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc ^ 0xFF


def can_crc(arbitration_id: int, dlc: int, payload: bytes) -> int:
    """Calculate the repository-defined CAN integrity byte over bytes 0-6."""
    if len(payload) < 7:
        raise ValueError("CAN payload must contain at least seven bytes")
    protected = bytes([arbitration_id & 0xFF, (arbitration_id >> 8) & 0xFF, dlc, *payload[:7]])
    return crc8_sae_j1850(protected)


def finalize_can_payload(arbitration_id: int, payload: bytes, *, dlc: int = 8) -> bytes:
    """Return an eight-byte payload with a freshly calculated CRC at byte 7."""
    if len(payload) != 8:
        raise ValueError("Synthetic CAN payloads must be exactly eight bytes")
    encoded = bytearray(payload)
    encoded[7] = can_crc(arbitration_id, dlc, bytes(encoded))
    return bytes(encoded)
