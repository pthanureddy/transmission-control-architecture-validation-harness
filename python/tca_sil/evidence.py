"""Structured, hashable evidence output for fault-tracing scenarios."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from tca_sil.models import TraceEvent

if TYPE_CHECKING:
    from tca_sil.harness import ScenarioOutcome


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class EvidenceRecorder:
    def __init__(self, scenario_id: str) -> None:
        self.scenario_id = scenario_id
        self.events: list[TraceEvent] = []

    def add(
        self,
        *,
        simulated_time_ms: int,
        event_type: str,
        source: str,
        arbitration_id: int | None = None,
        dlc: int | None = None,
        data: bytes | None = None,
        decoded: dict[str, object] | None = None,
        ingest_status: str | None = None,
        fault_code: str | None = None,
        note: str | None = None,
    ) -> None:
        self.events.append(
            TraceEvent(
                index=len(self.events) + 1,
                scenario_id=self.scenario_id,
                simulated_time_ms=simulated_time_ms,
                event_type=event_type,
                source=source,
                arbitration_id=f"0x{arbitration_id:03X}" if arbitration_id is not None else None,
                dlc=dlc,
                data_hex=data.hex().upper() if data is not None else None,
                decoded=decoded,
                ingest_status=ingest_status,
                fault_code=fault_code,
                note=note,
            )
        )

    def canonical_events(self) -> list[dict[str, object]]:
        return [
            {key: value for key, value in asdict(event).items() if value is not None}
            for event in self.events
        ]

    def deterministic_hash(self) -> str:
        return sha256_text(canonical_json(self.canonical_events()))

    def write(self, root: Path, outcome: ScenarioOutcome) -> dict[str, object]:
        scenario_dir = root / self.scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        events = self.canonical_events()
        trace_text = "".join(canonical_json(event) + "\n" for event in events)
        trace_path = scenario_dir / "trace.jsonl"
        trace_path.write_text(trace_text, encoding="utf-8", newline="\n")
        summary = outcome.to_dict()
        summary["trace_sha256"] = hashlib.sha256(trace_text.encode("utf-8")).hexdigest()
        summary_path = scenario_dir / "summary.json"
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return {
            "scenario_id": self.scenario_id,
            "passed": outcome.passed,
            "trace": str(trace_path.relative_to(root)).replace("\\", "/"),
            "summary": str(summary_path.relative_to(root)).replace("\\", "/"),
            "trace_sha256": summary["trace_sha256"],
        }


def write_manifest(root: Path, entries: list[dict[str, object]]) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    ordered = sorted(entries, key=lambda item: str(item["scenario_id"]))
    payload = {
        "schema_version": 1,
        "scenario_count": len(ordered),
        "passed_count": sum(bool(item["passed"]) for item in ordered),
        "entries": ordered,
    }
    path = root / "manifest.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return path
