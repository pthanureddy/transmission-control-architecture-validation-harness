# Requirement-to-Test Traceability

| Requirement | Architecture element | Named verification |
|---|---|---|
| SWR-001 | PlausibilityMonitor | `primary_throttle_range_is_checked`, `redundant_throttle_range_is_checked` |
| SWR-002 | PlausibilityMonitor | `speed_range_is_checked`, `shaft_speed_range_is_checked` |
| SWR-003 | PlausibilityMonitor / ControlApplication | `redundant_throttle_disagreement_is_detected`, `sensor_disagreement_forces_safe_output` |
| SWR-004 | PlausibilityMonitor | `stale_input_is_detected`, `future_timestamp_does_not_underflow` |
| SWR-005 | ShiftController | `drive_request_selects_first_gear_at_low_speed`, `drive_schedule_upshifts_with_speed`, `high_load_delays_upshift` |
| SWR-006 | ShiftController / ControlApplication | `reverse_is_rejected_while_moving_forward`, `park_is_rejected_at_speed`, `illegal_direction_change_reaches_safe_state` |
| SWR-007 | SafetySupervisor | `validation_fault_is_latched`, `first_fault_is_preserved`, `application_fault_remains_latched` |
| SWR-008 | ControlApplication | `sensor_disagreement_forces_safe_output` |
| SWR-009 | SafetySupervisor | `watchdog_overrun_is_latched` |
| SWR-010 | SafetySupervisor / ControlApplication | `reset_is_rejected_while_moving`, `reset_requires_brake`, `reset_is_accepted_at_safe_standstill`, `application_reset_recovers_on_next_cycle` |
| SWR-011 | ControlApplication | `output_sequence_increments` |
| SWR-012 | C CRC / ControlApplication | `crc_empty_payload_is_defined`, `crc_rejects_null_non_empty_payload`, `crc_is_deterministic`, `crc_changes_when_payload_changes`, `output_crc_is_reproducible` |

The CI scenario runner supplements the named checks by executing a Park-to-Drive cycle followed by an injected redundant-throttle disagreement and emitting the selected gear, mode, fault, torque limit, and CRC.

