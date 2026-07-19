# Software Architecture

## Component responsibilities

### PlausibilityMonitor

Validates physical ranges, redundant-throttle agreement, and input freshness. It returns a value object rather than changing control state.

### ShiftController

Owns the simplified direction and gear state. It applies a throttle-adjusted six-gear schedule and rejects Park/Reverse transitions above the configured speed threshold.

### SafetySupervisor

Arbitrates validation, architecture, and watchdog faults. The first fault is latched to keep the initiating cause observable. Reset requires valid inputs, applied brake, and near-zero speed.

### ControlApplication

Defines control-cycle ordering and the safe-state contract. It prevents an invalid frame from reaching gear calculation, delegates fault arbitration, forces Neutral with zero torque on a latched fault, increments the output sequence, and calls the C CRC boundary.

### C integrity boundary

`tca_crc8_sae_j1850` is a C11 module with an `extern "C"` header. It calculates an integrity byte over fixed output fields and demonstrates an explicit C/C++ interface.

## Control-cycle sequence

1. Validate input ranges, redundancy, and freshness.
2. If valid, calculate a direction/gear decision.
3. Evaluate validation, direction, and watchdog faults.
4. If a fault is latched, force the safe-state output contract.
5. Increment the diagnostic sequence and calculate the output CRC.

## Fault propagation

Faults are values, not exceptions. The first detected fault is preserved. The software uses a fail-safe output for this exercise: Neutral, zero torque limit, and shift inhibition. A real transmission safety concept might require a different degraded mode based on hazard analysis and vehicle state.

## Runtime and memory properties

- no heap allocation in the control-path implementation;
- fixed-size input, validation, decision, and output records;
- bounded branch-based control flow;
- explicit numeric limits through `QualityLimits`;
- no file, network, clock, or operating-system dependency in `tca_core`;
- no exceptions used by the runtime implementation.

## Verification seams

Each component exposes a small synchronous API. Tests can inject frame timestamps, execution duration, speed, redundant sensor differences, and direction transitions without hardware or time-dependent behavior.

