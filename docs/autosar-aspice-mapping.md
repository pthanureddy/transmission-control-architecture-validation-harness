# AUTOSAR and ASPICE Work-Product Mapping

## Boundary

This is an educational mapping, not AUTOSAR implementation experience and not evidence of ASPICE capability or assessment compliance.

## AUTOSAR Classic concept mapping

| Repository element | Closest conceptual area | What is missing |
|---|---|---|
| `ControlApplication` | Application software component behavior | ARXML, ports, runnables, RTE generation, calibration |
| `SensorFrame` / `ControlOutput` | Sender-receiver data exchange | Interfaces, data types, ComSpec, RTE events |
| `PlausibilityMonitor` | Application safety/monitoring component | AUTOSAR safety mechanisms and configured communication |
| `SafetySupervisor` | Supervision/degraded-state logic | Watchdog Manager, OS supervision, ECU state management |
| `safety_crc.c` | End-to-end integrity concept | AUTOSAR E2E profiles, counters, Data IDs, generated configuration |
| `QualityLimits` | Calibration/configuration values | NvM, generated parameters, variant management |

## ASPICE-style work-product mapping

| Engineering outcome | Repository artifact |
|---|---|
| System/software context and constraints | `docs/system-context.md` |
| Software requirements and quality goals | `docs/requirements.md` |
| Software architectural design | `docs/software-architecture.md` |
| Detailed implementation | `include/`, `src/`, `app/` |
| Unit and integration verification | `tests/test_main.cpp`, CTest |
| Bidirectional review aid | `docs/traceability.md` |
| Architecture decisions | `docs/adr/` |
| Quality assurance automation | CMake quality options and GitHub Actions |

Missing process evidence includes stakeholder baselines, change requests, reviews, independence, configuration audits, problem-resolution records, release criteria, and organizational process capability.

