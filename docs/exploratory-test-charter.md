# Exploratory Test Charter: Controller Boundaries

## Mission

Explore behavior immediately below, at, and above five configured controller limits. The goal is to expose ambiguous inclusivity, inconsistent safe-state behavior, or non-deterministic results that example-based requirement tests can miss.

## Scope and heuristics

The campaign uses synthetic CAN frames and the compiled C/C++ DUT through the existing C ABI. It probes:

- maximum vehicle speed: 259.9, 260.0, and 260.1 km/h;
- maximum redundant-throttle disagreement: 4.5, 5.0, and 5.5 percentage points;
- maximum input age: 99, 100, and 101 ms;
- control-cycle budget: 4,999, 5,000, and 5,001 us;
- forward-to-reverse direction change: 0.9, 1.0, and 1.1 km/h.

Each probe is executed twice. The campaign does not use wall-clock sleeps and does not assume a required fault transition in its pass/fail oracle. It records the observed transition and checks protocol completion, deterministic replay, and state invariants.

## Oracles

- Every paired input reaches `FRAME_READY` without a transport error.
- Repeated runs produce the same canonical trace hash.
- A `SAFE_STATE` result has a non-zero fault, Neutral gear, zero torque limit, and shift inhibition.
- A `NORMAL` result has no fault, full repository-defined torque limit, and no shift inhibition.

Unexpected transition points are findings for review, not automatically hidden by the tool. Confirmed requirements are converted to named regression checks in `tests/test_main.cpp`.

## Evidence and exit criteria

`scripts/run_exploratory_campaign.py` writes a generated probe catalog, per-probe JSONL traces, SHA-256 evidence manifests, `quality-status.json`, and `quality-status.md`. The CI campaign passes when all 15 probes complete twice with deterministic traces and no invariant anomaly.

## Evidence boundary

This is a scripted, time-boxed exploratory technique for a synthetic software-in-the-loop target. It is not testing on an ECU, physical CAN network, HIL bench, vehicle, RTOS, or production platform. The configured limits are repository values rather than OEM requirements.
