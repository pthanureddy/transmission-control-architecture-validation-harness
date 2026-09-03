# SIL Verified Baseline

## Local Python verification — 1 September 2026

The local Windows workspace had Python 3.11.9 but no CMake or C/C++ compiler. The following checks were executed against the SIL extension:

| Check | Result |
|---|---|
| pytest | 48 collected, 48 passed, 0 failed |
| Python core coverage | 97.73% combined line/branch coverage (459 statements, 70 branches; ctypes and Robot glue excluded) |
| Ruff format and lint | Passed |
| strict mypy | Passed, 11 source files checked |
| Requirement/catalog/Robot traceability | Passed: 10 requirements, 14 catalog scenarios, 14 catalog scenarios referenced by Robot |
| Python dependency audit | No known vulnerabilities after upgrading the environment's pip and setuptools; the editable local project was skipped because it is not a PyPI distribution |
| DBC smoke | Motion and driver frames encoded/decoded with the expected IDs, payload bytes, counters, and CRC values |

## Hosted native and acceptance verification - 1 September 2026

Public GitHub Actions run [33513245635](https://github.com/pthanureddy/transmission-control-architecture-validation-harness/actions/runs/33513245635) verified commit `409d62ae174f4391d8ff2608b7a7fe60ecf16cf1`.

| Check | Result |
|---|---|
| Compiled C/C++ verification | 3/3 CTest targets passed on Windows, Ubuntu/GCC, and Ubuntu/Clang |
| Robot Framework acceptance | 15/15 cases passed on Windows and Ubuntu against the compiled DUT bridge |
| Structured scenario evidence | 14/14 scenario evidence sets passed hash and verdict validation on both operating systems |
| Python tests and coverage | 48/48 pytest tests passed with 97.73% combined core coverage on Windows and Ubuntu |
| Static analysis and sanitizers | clang-tidy, cppcheck, AddressSanitizer, and UndefinedBehaviorSanitizer jobs passed |
| Dependency audit | No known vulnerabilities were reported by the Linux SIL job |

The local machine still had no CMake/compiler, so the native and Robot results above are attributed only to the linked public hosted run.

## Exploratory boundary verification - 3 September 2026

Public GitHub Actions run [33769087012](https://github.com/pthanureddy/transmission-control-architecture-validation-harness/actions/runs/33769087012) verified commit `39b6175a859acfd7d4b62a814ca737d8bab6705d`.

| Check | Result |
|---|---|
| Compiled C/C++ verification | The 47-check runner passed within 3/3 CTest targets on Windows, Ubuntu/GCC, and Ubuntu/Clang |
| Python tests and coverage | 51/51 tests passed with 97.48% combined Python-core line/branch coverage |
| Robot Framework acceptance | 15/15 cases passed against the compiled DUT on Windows and Ubuntu |
| Exploratory boundary campaign | 15/15 probes passed twice per environment; 60 hosted executions, deterministic traces, zero invariant anomalies |
| Quality and security gates | Ruff, strict mypy, traceability, clang-tidy, cppcheck, AddressSanitizer, UndefinedBehaviorSanitizer, and dependency audit passed |

The [dated session record](exploratory-session-2026-09-03.md) preserves the tested values, observed transitions, regression follow-up, and evidence boundary.
