# SIL Test-Automation Requirements

These requirements are derived for this repository's synthetic test environment. They are not OEM, customer, safety, or production requirements.

| ID | Requirement | Primary verification |
|---|---|---|
| SIL-REQ-001 | Equal initial state, catalog input, and simulated time shall produce byte-identical trace events. | `SIL-NOM-001` and Robot deterministic replay |
| SIL-REQ-002 | Motion and driver-request signals shall be encoded from the repository DBC and transported through an in-process `python-can` virtual interface. | `SIL-NOM-001`, `SIL-ORD-001`, codec tests |
| SIL-REQ-003 | The Python harness shall invoke the existing compiled C/C++ controller through the versioned C ABI rather than reimplementing the DUT for acceptance tests. | CTest bridge contract and all Robot scenarios |
| SIL-REQ-004 | The fault injector shall support CRC corruption, wrong DLC, unknown identifier, unsupported direction value, and rolling-counter mismatch. | `SIL-CRC-001`, `SIL-DLC-001`, `SIL-ID-001`, `SIL-SIG-001`, `SIL-SEQ-001` |
| SIL-REQ-005 | The harness shall expose each frame's ingress decision and shall exercise reversed arrival, dropped input, and delayed input without wall-clock sleeps. | `SIL-ORD-001`, `SIL-DROP-001`, `SIL-AGE-001` |
| SIL-REQ-006 | Acceptance scenarios shall verify the controller's safe-state response for plausibility, range, age, direction-change, and execution-budget faults. | `SIL-PLS-001`, `SIL-RNG-001`, `SIL-AGE-001`, `SIL-DIR-001`, `SIL-WDG-001` |
| SIL-REQ-007 | A safe-state oracle shall verify mode, selected gear, torque limit, shift inhibition, and latched fault. | All safe-state Robot scenarios |
| SIL-REQ-008 | Every scenario shall emit deterministic JSONL frame/events, a JSON verdict, and a manifest containing SHA-256 trace hashes. | All catalog scenarios and `validate_sil_evidence.py` |
| SIL-REQ-009 | The test-side diagnostic memory shall map a compiled-DUT fault to a project DTC with active/stored state, occurrence data, and an output snapshot. | Fault scenarios and Python diagnostic tests |
| SIL-REQ-010 | A later fault shall not replace the first fault reported by the controller. | `SIL-LAT-001` |

`scripts/check_sil_traceability.py` fails CI if a requirement is uncovered, a catalog scenario is absent from the Robot suite, or an unknown ID is referenced.
