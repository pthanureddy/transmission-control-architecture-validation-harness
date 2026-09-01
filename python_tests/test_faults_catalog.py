from __future__ import annotations

import json
from pathlib import Path

import can
import pytest
from tca_sil.catalog import load_catalog
from tca_sil.codec import CanCodec
from tca_sil.crc import can_crc
from tca_sil.faults import clone_message, inject_fault
from tca_sil.models import DirectionRequest, DriverSignals, MotionSignals


@pytest.fixture
def motion_message() -> can.Message:
    return CanCodec().encode_motion(MotionSignals(8.0, 1500.0, 400.0, 1), timestamp_ms=10)


def test_clone_preserves_unspecified_fields(motion_message: can.Message) -> None:
    cloned = clone_message(motion_message)
    assert cloned.arbitration_id == motion_message.arbitration_id
    assert cloned.dlc == motion_message.dlc
    assert bytes(cloned.data) == bytes(motion_message.data)


def test_drop_fault_removes_frame(motion_message: can.Message) -> None:
    assert inject_fault(motion_message, "drop", CanCodec()) is None


def test_crc_fault_changes_payload_without_repair(motion_message: can.Message) -> None:
    corrupted = inject_fault(motion_message, "corrupt_crc", CanCodec())
    assert corrupted is not None
    assert corrupted.data[7] != can_crc(corrupted.arbitration_id, corrupted.dlc, corrupted.data)


def test_length_fault_sets_dlc_to_seven(motion_message: can.Message) -> None:
    changed = inject_fault(motion_message, "wrong_dlc", CanCodec())
    assert changed is not None and changed.dlc == 7


def test_identifier_fault_uses_unknown_identifier(motion_message: can.Message) -> None:
    changed = inject_fault(motion_message, "unknown_identifier", CanCodec())
    assert changed is not None and changed.arbitration_id == 0x555


def test_invalid_direction_fault_recomputes_crc() -> None:
    codec = CanCodec()
    driver = codec.encode_driver(
        DriverSignals(20.0, 20.0, DirectionRequest.DRIVE, False, 1),
        timestamp_ms=10,
    )
    changed = inject_fault(driver, "invalid_direction", codec)
    assert changed is not None
    assert changed.data[2] == 7
    assert changed.data[7] == can_crc(changed.arbitration_id, changed.dlc, changed.data)


def test_unknown_fault_name_fails(motion_message: can.Message) -> None:
    with pytest.raises(ValueError, match="Unsupported fault"):
        inject_fault(motion_message, "invented", CanCodec())


def test_catalog_has_unique_traceable_scenarios() -> None:
    catalog = load_catalog()
    assert len(catalog) == 14
    assert all(spec["requirements"] for spec in catalog.values())


def test_catalog_rejects_duplicate_ids(tmp_path: Path) -> None:
    path = tmp_path / "catalog.json"
    scenario = {
        "id": "DUP",
        "title": "duplicate",
        "requirements": ["REQ"],
        "steps": [{}],
        "expected": {},
    }
    path.write_text(json.dumps({"scenarios": [scenario, scenario]}), encoding="utf-8")
    with pytest.raises(ValueError, match="unique"):
        load_catalog(path)


def test_catalog_rejects_empty_catalog(tmp_path: Path) -> None:
    path = tmp_path / "catalog.json"
    path.write_text('{"scenarios": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="at least one"):
        load_catalog(path)
