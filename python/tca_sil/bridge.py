"""ctypes boundary to the CMake-built C/C++ controller library."""

from __future__ import annotations

import ctypes
import os
import platform
from abc import ABC, abstractmethod
from pathlib import Path

import can

from tca_sil.models import DutResult, FaultCode, Gear, IngestStatus, OperatingMode


class DutAdapter(ABC):
    """Small interface that keeps harness tests independent of ctypes loading."""

    @abstractmethod
    def ingest(
        self,
        message: can.Message,
        *,
        reception_timestamp_ms: int,
        now_ms: int,
        execution_time_us: int,
    ) -> DutResult:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class _SilResult(ctypes.Structure):
    _fields_ = [
        ("output_sequence", ctypes.c_uint32),
        ("output_can_id", ctypes.c_uint16),
        ("ingest_status", ctypes.c_uint8),
        ("has_output", ctypes.c_uint8),
        ("output_dlc", ctypes.c_uint8),
        ("output_data", ctypes.c_uint8 * 8),
        ("selected_gear", ctypes.c_uint8),
        ("operating_mode", ctypes.c_uint8),
        ("fault_code", ctypes.c_uint8),
        ("torque_limit_pct", ctypes.c_uint8),
        ("shift_inhibited", ctypes.c_uint8),
    ]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def locate_sil_library(explicit: Path | None = None) -> Path:
    """Resolve the shared library, preferring an explicit path or environment variable."""
    if explicit is not None:
        candidates = [explicit]
    elif os.environ.get("TCA_SIL_LIBRARY"):
        candidates = [Path(os.environ["TCA_SIL_LIBRARY"])]
    else:
        root = repository_root()
        system = platform.system()
        if system == "Windows":
            candidates = [
                root / "build" / "Release" / "tca_sil.dll",
                root / "build" / "Debug" / "tca_sil.dll",
                root / "build" / "tca_sil.dll",
            ]
        elif system == "Darwin":
            candidates = [root / "build" / "libtca_sil.dylib"]
        else:
            candidates = [root / "build" / "libtca_sil.so"]

    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        if resolved.is_file():
            return resolved
    checked = ", ".join(str(item) for item in candidates)
    raise FileNotFoundError(
        "Compiled SIL library was not found. Build the CMake target "
        f"tca_sil_bridge or set TCA_SIL_LIBRARY. Checked: {checked}"
    )


class CtypesDutAdapter(DutAdapter):
    """Drive the real compiled controller through a fixed-width C ABI."""

    def __init__(self, library_path: Path | None = None) -> None:
        self.library_path = locate_sil_library(library_path)
        self._library = ctypes.CDLL(str(self.library_path))
        self._configure_signatures()
        if self._library.tca_sil_abi_version() != 1:
            raise RuntimeError("Unsupported tca_sil ABI version")
        self._session = self._library.tca_sil_create()
        if not self._session:
            raise MemoryError("The compiled DUT could not allocate a SIL session")

    def _configure_signatures(self) -> None:
        self._library.tca_sil_abi_version.argtypes = []
        self._library.tca_sil_abi_version.restype = ctypes.c_uint32
        self._library.tca_sil_create.argtypes = []
        self._library.tca_sil_create.restype = ctypes.c_void_p
        self._library.tca_sil_destroy.argtypes = [ctypes.c_void_p]
        self._library.tca_sil_destroy.restype = None
        self._library.tca_sil_reset.argtypes = [ctypes.c_void_p]
        self._library.tca_sil_reset.restype = ctypes.c_int32
        self._library.tca_sil_ingest.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint16,
            ctypes.c_uint8,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(_SilResult),
        ]
        self._library.tca_sil_ingest.restype = ctypes.c_int32

    def ingest(
        self,
        message: can.Message,
        *,
        reception_timestamp_ms: int,
        now_ms: int,
        execution_time_us: int,
    ) -> DutResult:
        if not self._session:
            raise RuntimeError("SIL session is closed")
        raw = bytes(message.data)
        if len(raw) > 8:
            raise ValueError("Classical synthetic CAN frames cannot exceed eight bytes")
        payload = (ctypes.c_uint8 * 8)(*(raw + bytes(8 - len(raw))))
        result = _SilResult()
        status = self._library.tca_sil_ingest(
            self._session,
            message.arbitration_id,
            message.dlc,
            payload,
            reception_timestamp_ms,
            now_ms,
            execution_time_us,
            ctypes.byref(result),
        )
        if status != 0:
            raise RuntimeError(f"tca_sil_ingest failed with status {status}")
        return self._to_result(result)

    @staticmethod
    def _to_result(result: _SilResult) -> DutResult:
        has_output = bool(result.has_output)
        return DutResult(
            ingest_status=IngestStatus(result.ingest_status),
            has_output=has_output,
            output_sequence=result.output_sequence,
            output_can_id=result.output_can_id,
            output_dlc=result.output_dlc,
            output_data=bytes(result.output_data) if has_output else b"",
            selected_gear=Gear(result.selected_gear) if has_output else None,
            operating_mode=OperatingMode(result.operating_mode) if has_output else None,
            fault_code=FaultCode(result.fault_code) if has_output else None,
            torque_limit_pct=result.torque_limit_pct,
            shift_inhibited=bool(result.shift_inhibited),
        )

    def reset(self) -> None:
        if not self._session:
            raise RuntimeError("SIL session is closed")
        status = self._library.tca_sil_reset(self._session)
        if status != 0:
            raise RuntimeError(f"tca_sil_reset failed with status {status}")

    def close(self) -> None:
        if self._session:
            self._library.tca_sil_destroy(self._session)
            self._session = None

    def __enter__(self) -> CtypesDutAdapter:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
