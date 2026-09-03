"""Run the time-boxed boundary campaign against the compiled SIL controller."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tca_sil.bridge import CtypesDutAdapter
from tca_sil.exploratory import run_boundary_campaign


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/exploratory"))
    arguments = parser.parse_args()
    result = run_boundary_campaign(CtypesDutAdapter(), arguments.output_dir)
    print(
        f"{result.status}: {result.probe_count} probes, "
        f"{result.execution_count} executions, {result.anomaly_count} anomalies"
    )
    print(result.markdown_report)
    return 0 if result.anomaly_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
