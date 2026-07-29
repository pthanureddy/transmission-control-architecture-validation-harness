# Software Architecture

## Component responsibilities

### CAN protocol boundary

`CanInputAssembler` validates two assigned 11-bit identifiers, an eight-byte payload contract, CRC-8, direction encoding, and a shared rolling sequence before assembling a `SensorFrame`. The output encoder maps the selected gear, mode, fault, torque limit, inhibition flag, and truncated sequence into a fixed-size CAN frame. The module models protocol behavior in memory; it does not open a CAN device.

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

1. Validate and pair the motion and driver-request CAN frames.
2. Validate decoded input ranges, redundancy, and freshness.
3. If valid, calculate a direction/gear decision.
4. Evaluate validation, direction, and watchdog faults.
5. If a fault is latched, force the safe-state output contract.
6. Increment the diagnostic sequence, calculate the application CRC, and encode the CAN output frame.

## Fault propagation

Faults are values, not exceptions. The first detected fault is preserved. The software uses a fail-safe output for this exercise: Neutral, zero torque limit, and shift inhibition. A real transmission safety concept might require a different degraded mode based on hazard analysis and vehicle state.

## Runtime and memory properties

- no heap allocation in the control-path implementation;
- fixed-size CAN, input, validation, decision, and output records;
- bounded branch-based control flow;
- explicit numeric limits through `QualityLimits`;
- no file, network, clock, or operating-system dependency in `tca_core`;
- no exceptions used by the runtime implementation.

## Verification seams

Each component exposes a small synchronous API. Tests can inject CAN corruption, frame mismatches, timestamps, execution duration, speed, redundant sensor differences, and direction transitions without hardware or time-dependent behavior.
