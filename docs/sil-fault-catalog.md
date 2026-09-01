# SIL Fault Catalogue

| Scenario | Injected or controlled condition | Expected observable behavior | Boundary |
|---|---|---|---|
| `SIL-CRC-001` | One payload bit changes after CRC generation. | `INVALID_CRC`; no control output. | Synthetic frame corruption. |
| `SIL-DLC-001` | Motion frame declares DLC 7. | `INVALID_LENGTH`; no control output. | Not a physical truncation. |
| `SIL-ID-001` | Motion frame uses identifier `0x555`. | `UNKNOWN_IDENTIFIER`; no control output. | Repository-defined IDs only. |
| `SIL-SIG-001` | Direction byte is changed to 7 and CRC recomputed. | `INVALID_SIGNAL`; no control output. | Signal-map negative test. |
| `SIL-SEQ-001` | Motion and driver counters differ. | `SEQUENCE_MISMATCH`; no control output. | Pairing check, not full rolling-counter supervision. |
| `SIL-DROP-001` | Motion frame is omitted. | Driver frame remains `WAITING_FOR_PAIR`; no output. | Does not model CAN bus-off or a timeout DTC. |
| `SIL-PLS-001` | Redundant throttle values differ by 20 percentage points. | `SENSOR_DISAGREEMENT`, Neutral, zero torque, shift inhibited. | Synthetic plausibility fault. |
| `SIL-RNG-001` | Vehicle speed is 300 km/h. | `INPUT_RANGE` safe state. | Boundary test, not sensor calibration. |
| `SIL-AGE-001` | Evaluation time is 120 ms after reception. | `STALE_INPUT` safe state. | Simulated time; no timing hardware. |
| `SIL-DIR-001` | Reverse is requested at 30 km/h after Drive. | `ILLEGAL_DIRECTION_CHANGE` safe state. | Simplified source-code rule. |
| `SIL-WDG-001` | Caller supplies 6,000 microseconds against a 5,000-microsecond budget. | `WATCHDOG_OVERRUN` safe state. | Injected duration, not measured execution time. |
| `SIL-LAT-001` | Sensor disagreement is followed by an illegal direction request. | First `SENSOR_DISAGREEMENT` remains latched. | Tests existing first-fault policy. |

The trace correlator identifies the first abnormal ingest status or first non-zero controller fault in the deterministic event sequence. It does not claim general root-cause diagnosis of a real vehicle.
