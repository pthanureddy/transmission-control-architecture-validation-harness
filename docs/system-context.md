# System Context and Constraints

## System concept

The exercise represents one software slice between synthetic vehicle inputs and a transmission actuation request. A caller provides a time-stamped frame containing vehicle speed, shaft speeds, two throttle values, brake status, and a direction request. The software returns a gear, operating mode, fault, torque limit, inhibition flag, sequence, and integrity byte.

## External actors

- **Driver-input adapter:** supplies direction, throttle, and brake data.
- **Vehicle-state adapter:** supplies speed and shaft-speed data.
- **Scheduler/watchdog:** provides the frame time and observed execution time.
- **Transmission actuator boundary:** consumes the selected gear, torque limit, and inhibition flag.
- **Diagnostic recorder:** consumes the sequence, fault, mode, and CRC.

No real bus, sensor, actuator, operating system, calibration store, or diagnostic protocol is implemented.

## Derived architectural drivers

1. Invalid or inconsistent inputs must not reach gear selection unchecked.
2. Direction changes with unacceptable vehicle speed must be rejected.
3. A detected fault must remain visible until an explicit, guarded reset.
4. The control path must be deterministic and avoid heap allocation.
5. Validation, functional control, and safety supervision must remain independently testable.
6. Outputs need simple sequencing and integrity evidence for downstream review.
7. Requirements, design decisions, and tests must be traceable in version control.

## Technical constraints

- C11 and C++20 are used to demonstrate a mixed-language boundary.
- The runner is single-threaded and platform-independent.
- Floating-point input values are used for readability, not production calibration fidelity.
- The default control-cycle budget is 5,000 microseconds; the runner passes a synthetic observed duration rather than measuring wall-clock execution.
- The shift schedule is fixed source code and is not a calibrated transmission map.

## Feasibility decisions

The repository focuses on architecture, failure behavior, and verification rather than plant dynamics. Implementing a transmission model, hydraulic actuation, real-time scheduling, ECU drivers, AUTOSAR RTE communication, or a functional-safety lifecycle would require tools, hardware, calibration data, and organizational evidence outside this exercise.

