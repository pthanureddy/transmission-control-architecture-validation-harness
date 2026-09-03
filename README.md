# Transmission Control Architecture Validation Harness

A deterministic C11/C++20 engineering exercise for decomposing a simplified transmission-control concept into software components, a fixed-size CAN protocol boundary, safety mechanisms, requirements, quality goals, architecture decisions, and executable verification. A Python 3.11 and Robot Framework software-in-the-loop (SIL) layer now drives the compiled controller through a C ABI, injects synthetic network and signal faults, and preserves structured fault-tracing evidence.

The harness encodes and assembles synthetic CAN frames, selects a simplified gear state, rejects unsafe direction changes, latches faults, enters a torque-inhibited safe state, protects output records with a C CRC implementation, and emits a repeatable execution trace. Robot scenarios cover nominal and reversed frame ordering plus CRC, DLC, identifier, signal, sequence, dropped-frame, plausibility, range, stale-input, direction-change, watchdog, and first-fault cases. A separate exploratory campaign probes five control limits immediately below, at, and above their configured boundaries.

## Evidence boundary

This repository is not a production transmission controller and does not run on ECU hardware, a physical CAN network, a vehicle, or a rig. It is not an AUTOSAR stack, an ASPICE assessment, an ISO 26262 safety case, a calibrated shift model, a MATLAB/Simulink model, or an RTOS integration. The DBC, DTC labels, timestamps, durations, frames, and faults are repository-defined and synthetic. CANoe, vTestStudio, CAPL, Jenkins, and proprietary automotive tools are not used. The documents map selected concepts and work products only so the limits remain reviewable.

## SIL fault-tracing layer

```text
Robot scenario -> Python keywords -> DBC codec/fault injector
                                     -> python-can VirtualBus
                                     -> ctypes C ABI
                                     -> compiled C/C++ CAN assembler/controller
                                     -> output oracle + diagnostic memory
                                     -> JSONL trace, JSON verdict, SHA-256 manifest
```

The virtual buses are process-local and operating-system independent. Scenario time is supplied explicitly, so stale-input and watchdog cases do not depend on sleeps. Robot acceptance tests always load the compiled shared library; a test-only Python reference adapter is limited to unit-testing automation plumbing and is never used for acceptance evidence.

## Architecture at a glance

```text
Synthetic motion + driver CAN frames
             |
             v
     CanInputAssembler ----- ID, DLC, CRC, sequence pairing
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
  CAN output frame / automated verification
```

The runtime library has no heap allocation in the control path, uses fixed-size records, returns explicit fault codes, and keeps validation, control, and supervision responsibilities separate.

## Implemented requirements

- input range, redundant-throttle agreement, and data-age validation;
- 11-bit CAN identifier, payload-length, CRC, signal, and sequence validation;
- pairing of motion and driver-request frames into one control-cycle input;
- deterministic drive-gear scheduling across six forward gears;
- speed-dependent Park/Reverse direction-change inhibition;
- first-fault latching and torque-inhibited Neutral safe state;
- watchdog-budget monitoring and guarded standstill reset;
- monotonically increasing output sequence and SAE J1850-style CRC-8;
- fixed-size control-output CAN encoding with an integrity byte;
- requirement-to-test traceability for 15 software requirements;
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

### Python and Robot Framework SIL verification

Prerequisites are Python 3.11 plus the CMake/compiler requirements above.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
powershell -ExecutionPolicy Bypass -File scripts/verify-sil.ps1
```

On a machine without CMake or a C/C++ compiler, the Python-only checks remain available:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-sil.ps1 -PythonOnly
```

That reduced command does not run the compiled DUT bridge or Robot acceptance suite. Complete SIL verification is performed by the Windows/Linux GitHub Actions matrix.

Run the scripted boundary campaign after building the shared library:

```powershell
python scripts/run_exploratory_campaign.py --output-dir artifacts/exploratory
```

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

- 47 named unit and integration checks in the custom deterministic test runner;
- 3 CTest targets: the 47-check suite, C ABI bridge contract, and executable CAN-to-control scenario trace;
- C11 and C++20 compilation with strict warnings treated as errors;
- Linux CI matrix for GCC and Clang;
- CI quality job for clang-tidy, cppcheck, AddressSanitizer, and UndefinedBehaviorSanitizer.
- 14 traceable deterministic SIL scenarios and 15 Robot Framework acceptance cases, including a repeatability check;
- 51 Python tests for the DBC/CRC, fault injection, catalog, diagnostic memory, exploratory campaign, evidence, and virtual-bus orchestration;
- 15 exploratory boundary probes executed twice with deterministic trace and state-invariant checks;
- 97.73 percent combined line/branch coverage for the Python core in the recorded local baseline, with ctypes and Robot integration glue excluded from that denominator and exercised in hosted integration instead;
- public GitHub Actions run [33513245635](https://github.com/pthanureddy/transmission-control-architecture-validation-harness/actions/runs/33513245635) passed the Windows/Linux compiled-DUT matrix: 3/3 CTest targets, 48/48 pytest tests at 97.73 percent core coverage, 15/15 Robot cases, and 14/14 structured scenario evidence sets; GCC/Clang, static-analysis, and sanitizer jobs also passed.

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
- [SIL requirements](docs/sil-requirements.md)
- [SIL architecture](docs/sil-architecture.md)
- [SIL test strategy](docs/sil-test-strategy.md)
- [SIL fault catalogue](docs/sil-fault-catalog.md)
- [Exploratory boundary test charter](docs/exploratory-test-charter.md)
- [SIL verified baseline](docs/sil-verified-baseline.md)

## Repository layout

```text
include/tca/       public C and C++ interfaces
src/               CAN, validation, control, supervision, orchestration, CRC
app/               deterministic CAN-to-control scenario runner
tests/             47 named unit and integration checks
python/tca_sil/    virtual-CAN harness, C ABI adapter, fault tracing, exploratory tooling
python_tests/      automation-core tests using a labelled test-only adapter
robot_tests/       compiled-DUT SIL acceptance cases
network/           repository-defined synthetic DBC
scenarios/         deterministic scenario catalogue and expected results
docs/              architecture, requirements, traceability, safety boundaries
.github/workflows/ build, test, static-analysis, and sanitizer gates
```

## License

MIT
