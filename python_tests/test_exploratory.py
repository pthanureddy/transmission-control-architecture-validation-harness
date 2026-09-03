from __future__ import annotations

import json
from pathlib import Path

from tca_sil.codec import CanCodec
from tca_sil.exploratory import CampaignResult, boundary_probes, run_boundary_campaign

from python_tests.support import ReferenceAdapter


def run_reference_campaign(tmp_path: Path) -> CampaignResult:
    codec = CanCodec()
    return run_boundary_campaign(
        ReferenceAdapter(codec),
        tmp_path / "exploratory",
        codec=codec,
    )


def test_probe_catalog_covers_five_boundaries() -> None:
    probes = boundary_probes()
    assert len(probes) == 15
    assert {probe.dimension for probe in probes} == {
        "vehicle_speed_limit",
        "throttle_disagreement_limit",
        "input_age_limit",
        "execution_budget_limit",
        "direction_change_speed_limit",
    }


def test_campaign_repeats_probes_and_observes_expected_transitions(tmp_path: Path) -> None:
    result = run_reference_campaign(tmp_path)
    observed = {(item.dimension, item.value): item.fault for item in result.observations}
    assert result.status == "PASS"
    assert result.probe_count == 15
    assert result.execution_count == 30
    assert result.anomaly_count == 0
    assert observed[("vehicle_speed_limit", 260.0)] == "NONE"
    assert observed[("vehicle_speed_limit", 260.1)] == "INPUT_RANGE"
    assert observed[("throttle_disagreement_limit", 5.0)] == "NONE"
    assert observed[("throttle_disagreement_limit", 5.5)] == "SENSOR_DISAGREEMENT"
    assert observed[("input_age_limit", 100.0)] == "NONE"
    assert observed[("input_age_limit", 101.0)] == "STALE_INPUT"
    assert observed[("execution_budget_limit", 5000.0)] == "NONE"
    assert observed[("execution_budget_limit", 5001.0)] == "WATCHDOG_OVERRUN"
    assert observed[("direction_change_speed_limit", 1.0)] == "NONE"
    assert observed[("direction_change_speed_limit", 1.1)] == "ILLEGAL_DIRECTION_CHANGE"
    assert all(item.deterministic for item in result.observations)


def test_campaign_writes_machine_and_human_readable_quality_status(tmp_path: Path) -> None:
    result = run_reference_campaign(tmp_path)
    payload = json.loads(result.json_report.read_text(encoding="utf-8"))
    report = result.markdown_report.read_text(encoding="utf-8")
    assert payload["status"] == "PASS"
    assert payload["probe_count"] == 15
    assert payload["execution_count"] == 30
    assert payload["anomaly_count"] == 0
    assert "Exploratory Boundary Campaign Quality Status" in report
    assert "vehicle_speed_limit" in report
    assert (tmp_path / "exploratory" / "evidence" / "manifest.json").is_file()
