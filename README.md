# Transmission Control Architecture Validation Harness

A deterministic C11/C++20 engineering exercise for decomposing a simplified transmission-control concept into software components, safety mechanisms, requirements, quality goals, architecture decisions, and executable verification.

The harness processes synthetic redundant sensor frames, selects a simplified gear state, rejects unsafe direction changes, latches faults, enters a torque-inhibited safe state, protects output records with a C CRC implementation, and emits a repeatable execution trace.

## Evidence boundary

This repository is not a production transmission controller and does not run on ECU hardware. It is not an AUTOSAR stack, an ASPICE assessment, an ISO 26262 safety case, a calibrated shift model, a MATLAB/Simulink model, or an RTOS integration. The documents map selected concepts and work products only so the limits remain reviewable.

## Architecture at a glance

```text
Synthetic sensor/driver frame
             |
             v
  PlausibilityMonitor ---- range, redundancy, freshness
             |
             v
     ShiftController ----- direction constraints + shift schedule
             |
             v
    SafetySupervisor ----- first-fault latch + watchdog + reset guard
             |
             v
    ControlApplication --- safe-state arbitration + sequence + C CRC
             |
             v
  Trace / automated verification
```

The runtime library has no heap allocation in the control path, uses fixed-size records, returns explicit fault codes, and keeps validation, control, and supervision responsibilities separate.

## Implemented requirements

- input range, redundant-throttle agreement, and data-age validation;
- deterministic drive-gear scheduling across six forward gears;
- speed-dependent Park/Reverse direction-change inhibition;
- first-fault latching and torque-inhibited Neutral safe state;
- watchdog-budget monitoring and guarded standstill reset;
- monotonically increasing output sequence and SAE J1850-style CRC-8;
- requirement-to-test traceability for 12 software requirements;
- compiler warnings as errors, clang-tidy, cppcheck, sanitizers, CTest, and CI.

## Build and run

Prerequisites: CMake 3.20+ and a C11/C++20 compiler.

```powershell
cmake -S . -B build -DTCA_WARNINGS_AS_ERRORS=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
./build/transmission_architecture_runner
```

On multi-config Windows generators, run `./build/Debug/transmission_architecture_runner.exe` after building the Debug configuration.

## Quality checks

```bash
cmake -S . -B build-tidy -DTCA_ENABLE_CLANG_TIDY=ON
cmake --build build-tidy --parallel

cppcheck --enable=warning,style,performance,portability \
  --error-exitcode=1 --std=c++20 --suppress=missingIncludeSystem \
  include src app tests

cmake -S . -B build-sanitized -DTCA_ENABLE_SANITIZERS=ON
cmake --build build-sanitized --parallel
ctest --test-dir build-sanitized --output-on-failure
```

## Verification snapshot

- 32 named unit and integration checks in the custom deterministic test runner;
- 2 CTest targets: the 32-check suite and an executable scenario trace;
- C11 and C++20 compilation with strict warnings treated as errors;
- Linux CI matrix for GCC and Clang;
- CI quality job for clang-tidy, cppcheck, AddressSanitizer, and UndefinedBehaviorSanitizer.

The measured results above describe this repository only. They do not establish production safety, timing, calibration, hardware compatibility, or standards compliance.

## Documentation

- [System context and constraints](docs/system-context.md)
- [Software architecture](docs/software-architecture.md)
- [Software requirements and quality goals](docs/requirements.md)
- [Requirement-to-test traceability](docs/traceability.md)
- [Educational safety concept](docs/safety-concept.md)
- [AUTOSAR and ASPICE work-product mapping](docs/autosar-aspice-mapping.md)
- [Limitations](docs/limitations.md)
- [Architecture decisions](docs/adr/)

## Repository layout

```text
include/tca/       public C and C++ interfaces
src/               validation, control, supervision, orchestration, CRC
app/               deterministic scenario runner
tests/             32 named unit and integration checks
docs/              architecture, requirements, traceability, safety boundaries
.github/workflows/ build, test, static-analysis, and sanitizer gates
```

## License

MIT

