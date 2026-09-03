# Exploratory Boundary Session - 3 September 2026

## Session record

- Charter: [Controller boundaries](exploratory-test-charter.md)
- Code under test: commit `39b6175a859acfd7d4b62a814ca737d8bab6705d`
- Hosted evidence: [GitHub Actions run 33769087012](https://github.com/pthanureddy/transmission-control-architecture-validation-harness/actions/runs/33769087012)
- Environments: Ubuntu with the compiled GCC target and Windows with the compiled MSVC target
- Scope: 15 probes around five limits, each executed twice per environment
- Result: PASS on both environments; 30 executions per environment, 60 total, zero invariant anomalies

## Observations

| Focus | At the configured limit | First probed value above the limit | Observed transition |
|---|---:|---:|---|
| Vehicle speed | 260.0 km/h: Normal | 260.1 km/h | `INPUT_RANGE` SafeState |
| Throttle disagreement | 5.0 percentage points: Normal | 5.5 percentage points | `SENSOR_DISAGREEMENT` SafeState |
| Input age | 100 ms: Normal | 101 ms | `STALE_INPUT` SafeState |
| Execution budget | 5,000 us: Normal | 5,001 us | `WATCHDOG_OVERRUN` SafeState |
| Drive-to-Reverse change | 1.0 km/h: accepted | 1.1 km/h | `ILLEGAL_DIRECTION_CHANGE` SafeState |

Every repeated probe produced the same canonical trace hash. Every fault transition produced Neutral, zero torque, and shift inhibition. No unexpected transition or state-invariant issue was observed in this constrained session.

## Regression follow-up

The five confirmed inclusive/exclusive boundaries were added as named checks in `tests/test_main.cpp`. The resulting 47-check C/C++ test target passed through CTest on Windows, Ubuntu/GCC, and Ubuntu/Clang. The campaign is also covered by 51 Python tests and generates machine-readable JSON plus a Markdown quality-status report.

## Limitations

The session used synthetic CAN frames and a host-compiled SIL target. It did not use an ECU, physical CAN network, HIL bench, vehicle, RTOS, or production data. The observed transitions apply only to the repository-defined limits and controller.
