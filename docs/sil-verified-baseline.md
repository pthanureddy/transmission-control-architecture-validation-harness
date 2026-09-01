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

## Native and acceptance verification status

The local machine could not compile or execute the new shared-library bridge. Consequently, these results are deliberately **not** claimed in the local baseline:

- CMake configuration or C/C++ build of the new bridge;
- the new native CTest bridge-contract target;
- the 15 Robot Framework cases against the compiled DUT;
- Windows/Linux cross-platform behavior for the extension;
- a hosted CI result for the extension.

The GitHub Actions SIL matrix is configured to perform those checks on both Windows and Linux and to upload the Robot and structured evidence. Update this file only after the hosted run has actually completed.
