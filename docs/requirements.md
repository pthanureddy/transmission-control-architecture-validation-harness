# Software Requirements and Quality Goals

The requirements below are derived for this repository from the simplified system context. They are not customer or production requirements.

| ID | Software requirement | Verification |
|---|---|---|
| SWR-001 | The monitor shall reject throttle values outside 0-100 percent. | Unit test |
| SWR-002 | The monitor shall reject vehicle or shaft speeds outside configured ranges. | Unit test |
| SWR-003 | The monitor shall reject redundant-throttle disagreement above the configured limit. | Unit/integration test |
| SWR-004 | The monitor shall reject input older than the configured age. | Unit test |
| SWR-005 | The controller shall select one of six forward gears from speed and throttle load. | Unit test |
| SWR-006 | The controller shall inhibit Park or Reverse transitions above the configured speed. | Unit/integration test |
| SWR-007 | The supervisor shall latch the first detected fault. | Unit test |
| SWR-008 | The application shall command Neutral, zero torque, and shift inhibition in SafeState. | Integration test |
| SWR-009 | The supervisor shall detect execution duration above the configured cycle budget. | Unit test |
| SWR-010 | Fault reset shall require valid input, applied brake, and near-zero speed. | Unit/integration test |
| SWR-011 | Each output shall contain a monotonically increasing sequence number. | Integration test |
| SWR-012 | Each output shall contain a deterministic CRC over safety-relevant output fields. | C unit/integration test |

## Quality goals

| ID | Goal | Implemented evidence |
|---|---|---|
| QG-001 Determinism | Equal initial state and equal inputs produce equal output fields. | Synchronous APIs, injected time/duration, reproducible CRC test |
| QG-002 Testability | Components can be verified without hardware or network services. | Separate monitor/controller/supervisor APIs and 32 named checks |
| QG-003 Failure visibility | The initiating fault remains observable until guarded reset. | First-fault latch and diagnostic output |
| QG-004 Portability | The library builds with GCC and Clang using standard C11/C++20. | CI compiler matrix |
| QG-005 Code quality | Warnings and selected static-analysis findings fail CI. | `-Werror`, clang-tidy, cppcheck |
| QG-006 Runtime safety checks | Memory and undefined-behavior defects are checked in CI. | AddressSanitizer and UndefinedBehaviorSanitizer job |
| QG-007 Traceability | Requirements map to named automated tests and design elements. | `docs/traceability.md` |

