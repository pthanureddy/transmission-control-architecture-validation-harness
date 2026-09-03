# SIL Test Strategy

## Test levels

1. **C/C++ component and integration checks:** the original deterministic 42-check runner remains unchanged.
2. **Native bridge contract:** `tca_sil_bridge_contract` confirms the shared-library ABI calls the real CAN assembler and controller.
3. **Python unit and harness tests:** codec, CRC, mutation, catalog validation, diagnostic memory, evidence hashing, virtual-bus orchestration, and result oracles. Harness plumbing tests use a clearly labelled test-only reference adapter because they must run without a local compiler; they do not count as compiled-DUT verification.
4. **Robot Framework acceptance tests:** all catalog scenarios load `tca_sil.dll` or `libtca_sil.so` and therefore execute the compiled DUT. These are the project-level SIL results.
5. **Exploratory boundary campaign:** fifteen probes run below, at, and above five controller limits. Each probe is repeated against the compiled DUT, with transition observations, deterministic trace hashes, and state-invariant checks written as quality-status evidence.

## CI gates

- C11/C++20 build with warnings as errors on GCC and Clang;
- CTest plus existing clang-tidy, cppcheck, AddressSanitizer, and UndefinedBehaviorSanitizer jobs;
- Windows and Linux SIL matrix using Python 3.11;
- Ruff formatting/linting, strict mypy, and requirement/scenario traceability;
- pytest with a 90 percent line-plus-branch combined gate for Python core modules (ctypes and Robot glue are integration-tested instead and excluded from this coverage denominator);
- Robot `output.xml`, `log.html`, `report.html`, and xUnit output;
- JSON evidence/hash validation and Python dependency audit;
- exploratory boundary quality status for 15 probes and 30 repeated compiled-DUT executions;
- uploaded CI artifacts for each operating system.

## Acceptance rule

A scenario passes only when the complete ordered ingress-status list, output count, and every specified final field match. Fault scenarios additionally validate the expected project DTC when an output fault exists. Evidence validation fails if any scenario verdict is false, a trace hash differs, or a referenced artifact is missing.

## Reproduction

On Windows with Python 3.11, CMake, and a C/C++ compiler:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-sil.ps1
```

Python-only checks can run where the native toolchain is unavailable:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify-sil.ps1 -PythonOnly
```

The Python-only path does not execute the compiled bridge or Robot SIL cases and must not be reported as complete project verification.

The exploratory charter and evidence boundary are documented in [exploratory-test-charter.md](exploratory-test-charter.md). The campaign complements requirement-based tests; it does not represent physical-rig or vehicle exploration.
