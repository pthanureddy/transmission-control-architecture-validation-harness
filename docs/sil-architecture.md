# SIL Test-Automation Architecture

## Purpose

The SIL layer exercises the existing controller as a compiled shared library while keeping stimuli, time, fault injection, oracles, and evidence in Python. Robot Framework provides readable acceptance cases. This makes the test boundary explicit: the test code may inspect the result, but it does not replace the C/C++ control logic.

```text
Robot Framework scenario
          |
          v
Python keyword library ---- scenario catalog + deterministic simulated time
          |
          v
DBC codec -> fault injector -> python-can VirtualBus (input channel)
                                      |
                                      v
                              ctypes C ABI bridge
                                      |
                                      v
                         existing C/C++ CAN assembler
                                      |
                                      v
                         existing C/C++ controller
                                      |
                                      v
python-can VirtualBus (output channel) -> oracle -> diagnostic memory
                                                -> JSONL trace + JSON verdict
                                                -> SHA-256 evidence manifest
```

## Component responsibilities

- `tca_sil_bridge` exposes an opaque session and fixed-width C result record. It owns the existing `CanInputAssembler` and `ControlApplication`; it does not add alternate control behavior.
- `CanCodec` loads `network/tca_synthetic.dbc`, encodes the two input messages, decodes controller output, and calculates the same repository-defined CRC-8 as the C implementation.
- `ScenarioHarness` creates two isolated, in-process virtual CAN channels, advances catalog-supplied time, sends frames, invokes the compiled bridge, and applies explicit expected-result oracles.
- `faults.py` performs bounded, reviewable mutations: drop, CRC corruption, wrong DLC, unknown identifier, and invalid direction. Rolling-counter mismatch and delay are scenario inputs.
- `DiagnosticMemory` is a test-side fault record. It maps the controller's existing fault enum to project-specific DTC labels and implements a guarded clear rule; it is not a UDS server.
- `EvidenceRecorder` records raw bytes, decoded signals where possible, ingress status, controller fault, and first-fault correlation without wall-clock values. That makes repeated traces hash-stable.

## Determinism and isolation

The `python-can` virtual backend is process-local, so the Python nodes and bridge orchestration intentionally run in one Python process. Each harness receives unique input and output channel names. The C++ controller receives explicit reception time, evaluation time, and execution duration; the test suite uses no timing sleeps to create fault conditions.

## C ABI boundary

`include/tca/sil_api.h` is C-compatible and uses fixed-width fields. ABI version 1 supports create, reset, ingest, and destroy operations. The Python adapter checks the ABI version before creating a session. A dedicated CTest target validates nominal paired input, corrupt-frame rejection, reset, and output-frame shape at the native boundary.
