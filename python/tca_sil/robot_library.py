"""Robot Framework keywords for compiled-DUT SIL acceptance testing."""

from __future__ import annotations

import os
from pathlib import Path

from robot.api.deco import keyword, library

from tca_sil.bridge import CtypesDutAdapter
from tca_sil.harness import ScenarioHarness, ScenarioOutcome


@library(scope="SUITE", auto_keywords=False)
class TcaSilRobotLibrary:
    def __init__(self, artifact_root: str = "robot-output/sil") -> None:
        self.artifact_root = Path(artifact_root)
        self._harness: ScenarioHarness | None = None

    @keyword("Start SIL Session")
    def start_sil_session(self) -> None:
        if self._harness is not None:
            raise RuntimeError("SIL session is already active")
        library = os.environ.get("TCA_SIL_LIBRARY")
        adapter = CtypesDutAdapter(Path(library) if library else None)
        self._harness = ScenarioHarness(adapter, artifact_root=self.artifact_root)

    @keyword("Run SIL Scenario")
    def run_sil_scenario(self, scenario_id: str) -> dict[str, object]:
        outcome = self._require_harness().execute(scenario_id)
        self._assert_passed(outcome)
        return outcome.to_dict()

    @keyword("SIL Scenario Should Be Deterministic")
    def sil_scenario_should_be_deterministic(self, scenario_id: str) -> None:
        first = self._require_harness().execute(scenario_id)
        second = self._require_harness().execute(scenario_id)
        self._assert_passed(first)
        self._assert_passed(second)
        if first.deterministic_trace_hash != second.deterministic_trace_hash:
            raise AssertionError(
                f"{scenario_id} produced different trace hashes: "
                f"{first.deterministic_trace_hash} != {second.deterministic_trace_hash}"
            )

    @keyword("Close SIL Session")
    def close_sil_session(self) -> None:
        if self._harness is not None:
            self._harness.close()
            self._harness = None

    def _require_harness(self) -> ScenarioHarness:
        if self._harness is None:
            raise RuntimeError("Start SIL Session must run before scenario keywords")
        return self._harness

    @staticmethod
    def _assert_passed(outcome: ScenarioOutcome) -> None:
        if not outcome.passed:
            raise AssertionError(f"{outcome.scenario_id} failed: {'; '.join(outcome.failures)}")
