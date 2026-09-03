#include "tca/can_protocol.hpp"
#include "tca/control_application.hpp"
#include "tca/plausibility_monitor.hpp"
#include "tca/safety_crc.h"
#include "tca/safety_supervisor.hpp"
#include "tca/shift_controller.hpp"

#include <array>
#include <cstdint>
#include <iostream>

namespace {

#define CHECK_TRUE(expression)                                                               \
    do {                                                                                     \
        if (!(expression)) {                                                                 \
            std::cerr << "check failed at line " << __LINE__ << ": " #expression << '\n'; \
            return false;                                                                    \
        }                                                                                    \
    } while (false)

#define CHECK_EQ(actual, expected) CHECK_TRUE((actual) == (expected))

tca::SensorFrame valid_frame() {
    return {1U, 100U, 0.0, 800.0, 0.0, 10.0, 10.5, true, tca::DirectionRequest::Park};
}

bool crc_empty_payload_is_defined() {
    CHECK_EQ(tca_crc8_sae_j1850(nullptr, 0U), 0U);
    return true;
}

bool crc_rejects_null_non_empty_payload() {
    CHECK_EQ(tca_crc8_sae_j1850(nullptr, 1U), 0U);
    return true;
}

bool crc_is_deterministic() {
    const std::array<std::uint8_t, 4U> data{1U, 2U, 3U, 4U};
    CHECK_EQ(tca_crc8_sae_j1850(data.data(), data.size()),
             tca_crc8_sae_j1850(data.data(), data.size()));
    return true;
}

bool crc_changes_when_payload_changes() {
    const std::array<std::uint8_t, 4U> first{1U, 2U, 3U, 4U};
    const std::array<std::uint8_t, 4U> second{1U, 2U, 3U, 5U};
    CHECK_TRUE(tca_crc8_sae_j1850(first.data(), first.size()) !=
               tca_crc8_sae_j1850(second.data(), second.size()));
    return true;
}

bool valid_inputs_are_accepted() {
    const tca::PlausibilityMonitor monitor{};
    CHECK_TRUE(monitor.validate(valid_frame(), 100U).valid);
    return true;
}

bool primary_throttle_range_is_checked() {
    auto frame = valid_frame();
    frame.throttle_primary_pct = 101.0;
    const auto result = tca::PlausibilityMonitor{}.validate(frame, 100U);
    CHECK_EQ(result.fault, tca::FaultCode::InputRange);
    return true;
}

bool redundant_throttle_range_is_checked() {
    auto frame = valid_frame();
    frame.throttle_redundant_pct = -0.1;
    const auto result = tca::PlausibilityMonitor{}.validate(frame, 100U);
    CHECK_EQ(result.fault, tca::FaultCode::InputRange);
    return true;
}

bool speed_range_is_checked() {
    auto frame = valid_frame();
    frame.vehicle_speed_kph = 261.0;
    const auto result = tca::PlausibilityMonitor{}.validate(frame, 100U);
    CHECK_EQ(result.fault, tca::FaultCode::InputRange);
    return true;
}

bool shaft_speed_range_is_checked() {
    auto frame = valid_frame();
    frame.input_shaft_rpm = 12001.0;
    const auto result = tca::PlausibilityMonitor{}.validate(frame, 100U);
    CHECK_EQ(result.fault, tca::FaultCode::InputRange);
    return true;
}

bool redundant_throttle_disagreement_is_detected() {
    auto frame = valid_frame();
    frame.throttle_redundant_pct = 20.0;
    const auto result = tca::PlausibilityMonitor{}.validate(frame, 100U);
    CHECK_EQ(result.fault, tca::FaultCode::SensorDisagreement);
    return true;
}

bool stale_input_is_detected() {
    auto frame = valid_frame();
    frame.timestamp_ms = 100U;
    const auto result = tca::PlausibilityMonitor{}.validate(frame, 201U);
    CHECK_EQ(result.fault, tca::FaultCode::StaleInput);
    return true;
}

bool future_timestamp_does_not_underflow() {
    auto frame = valid_frame();
    frame.timestamp_ms = 200U;
    CHECK_TRUE(tca::PlausibilityMonitor{}.validate(frame, 100U).valid);
    return true;
}

bool speed_limit_boundary_is_inclusive() {
    auto frame = valid_frame();
    frame.vehicle_speed_kph = 260.0;
    CHECK_TRUE(tca::PlausibilityMonitor{}.validate(frame, 100U).valid);
    frame.vehicle_speed_kph = 260.1;
    CHECK_EQ(tca::PlausibilityMonitor{}.validate(frame, 100U).fault,
             tca::FaultCode::InputRange);
    return true;
}

bool throttle_disagreement_boundary_is_inclusive() {
    auto frame = valid_frame();
    frame.throttle_primary_pct = 20.0;
    frame.throttle_redundant_pct = 25.0;
    CHECK_TRUE(tca::PlausibilityMonitor{}.validate(frame, 100U).valid);
    frame.throttle_redundant_pct = 25.5;
    CHECK_EQ(tca::PlausibilityMonitor{}.validate(frame, 100U).fault,
             tca::FaultCode::SensorDisagreement);
    return true;
}

bool input_age_boundary_is_inclusive() {
    auto frame = valid_frame();
    frame.timestamp_ms = 100U;
    CHECK_TRUE(tca::PlausibilityMonitor{}.validate(frame, 200U).valid);
    CHECK_EQ(tca::PlausibilityMonitor{}.validate(frame, 201U).fault,
             tca::FaultCode::StaleInput);
    return true;
}

bool watchdog_budget_boundary_is_inclusive() {
    tca::SafetySupervisor at_limit{};
    at_limit.evaluate({true, tca::FaultCode::None}, tca::FaultCode::None, 5000U);
    CHECK_EQ(at_limit.mode(), tca::OperatingMode::Normal);

    tca::SafetySupervisor above_limit{};
    above_limit.evaluate({true, tca::FaultCode::None}, tca::FaultCode::None, 5001U);
    CHECK_EQ(above_limit.mode(), tca::OperatingMode::SafeState);
    CHECK_EQ(above_limit.latched_fault(), tca::FaultCode::WatchdogOverrun);
    return true;
}

bool direction_change_speed_boundary_is_inclusive() {
    tca::ShiftController at_limit{};
    auto frame = valid_frame();
    frame.vehicle_speed_kph = 1.0;
    frame.direction_request = tca::DirectionRequest::Drive;
    CHECK_EQ(at_limit.update(frame).fault, tca::FaultCode::None);
    frame.direction_request = tca::DirectionRequest::Reverse;
    CHECK_EQ(at_limit.update(frame).fault, tca::FaultCode::None);

    tca::ShiftController above_limit{};
    frame.vehicle_speed_kph = 1.1;
    frame.direction_request = tca::DirectionRequest::Drive;
    CHECK_EQ(above_limit.update(frame).fault, tca::FaultCode::None);
    frame.direction_request = tca::DirectionRequest::Reverse;
    CHECK_EQ(above_limit.update(frame).fault,
             tca::FaultCode::IllegalDirectionChange);
    return true;
}

bool controller_starts_in_park() {
    CHECK_EQ(tca::ShiftController{}.current_gear(), tca::Gear::Park);
    return true;
}

bool drive_request_selects_first_gear_at_low_speed() {
    tca::ShiftController controller{};
    auto frame = valid_frame();
    frame.direction_request = tca::DirectionRequest::Drive;
    frame.vehicle_speed_kph = 8.0;
    CHECK_EQ(controller.update(frame).gear, tca::Gear::First);
    return true;
}

bool drive_schedule_upshifts_with_speed() {
    tca::ShiftController controller{};
    auto frame = valid_frame();
    frame.direction_request = tca::DirectionRequest::Drive;
    frame.vehicle_speed_kph = 55.0;
    CHECK_EQ(controller.update(frame).gear, tca::Gear::Fourth);
    return true;
}

bool high_load_delays_upshift() {
    tca::ShiftController low_load{};
    tca::ShiftController high_load{};
    auto frame = valid_frame();
    frame.direction_request = tca::DirectionRequest::Drive;
    frame.vehicle_speed_kph = 32.0;
    frame.throttle_primary_pct = 20.0;
    const auto low_load_gear = low_load.update(frame).gear;
    frame.throttle_primary_pct = 80.0;
    const auto high_load_gear = high_load.update(frame).gear;
    CHECK_EQ(low_load_gear, tca::Gear::Third);
    CHECK_EQ(high_load_gear, tca::Gear::Second);
    return true;
}

bool reverse_is_allowed_at_standstill() {
    tca::ShiftController controller{};
    auto frame = valid_frame();
    frame.direction_request = tca::DirectionRequest::Reverse;
    CHECK_EQ(controller.update(frame).gear, tca::Gear::Reverse);
    return true;
}

bool reverse_is_rejected_while_moving_forward() {
    tca::ShiftController controller{};
    auto frame = valid_frame();
    frame.direction_request = tca::DirectionRequest::Drive;
    frame.vehicle_speed_kph = 20.0;
    CHECK_EQ(controller.update(frame).fault, tca::FaultCode::None);
    frame.direction_request = tca::DirectionRequest::Reverse;
    CHECK_EQ(controller.update(frame).fault, tca::FaultCode::IllegalDirectionChange);
    return true;
}

bool park_is_rejected_at_speed() {
    tca::ShiftController controller{};
    auto frame = valid_frame();
    frame.direction_request = tca::DirectionRequest::Drive;
    frame.vehicle_speed_kph = 30.0;
    (void)controller.update(frame);
    frame.direction_request = tca::DirectionRequest::Park;
    CHECK_EQ(controller.update(frame).fault, tca::FaultCode::IllegalDirectionChange);
    return true;
}

bool validation_fault_is_latched() {
    tca::SafetySupervisor supervisor{};
    supervisor.evaluate({false, tca::FaultCode::InputRange}, tca::FaultCode::None, 100U);
    CHECK_EQ(supervisor.mode(), tca::OperatingMode::SafeState);
    CHECK_EQ(supervisor.latched_fault(), tca::FaultCode::InputRange);
    return true;
}

bool watchdog_overrun_is_latched() {
    tca::SafetySupervisor supervisor{};
    supervisor.evaluate({true, tca::FaultCode::None}, tca::FaultCode::None, 5001U);
    CHECK_EQ(supervisor.latched_fault(), tca::FaultCode::WatchdogOverrun);
    return true;
}

bool first_fault_is_preserved() {
    tca::SafetySupervisor supervisor{};
    supervisor.evaluate({false, tca::FaultCode::StaleInput}, tca::FaultCode::None, 100U);
    supervisor.evaluate({false, tca::FaultCode::InputRange}, tca::FaultCode::None, 100U);
    CHECK_EQ(supervisor.latched_fault(), tca::FaultCode::StaleInput);
    return true;
}

bool reset_is_rejected_while_moving() {
    tca::SafetySupervisor supervisor{};
    supervisor.evaluate({false, tca::FaultCode::InputRange}, tca::FaultCode::None, 100U);
    auto frame = valid_frame();
    frame.vehicle_speed_kph = 2.0;
    CHECK_TRUE(!supervisor.request_reset(frame, {true, tca::FaultCode::None}));
    return true;
}

bool reset_requires_brake() {
    tca::SafetySupervisor supervisor{};
    supervisor.evaluate({false, tca::FaultCode::InputRange}, tca::FaultCode::None, 100U);
    auto frame = valid_frame();
    frame.brake_applied = false;
    CHECK_TRUE(!supervisor.request_reset(frame, {true, tca::FaultCode::None}));
    return true;
}

bool reset_is_accepted_at_safe_standstill() {
    tca::SafetySupervisor supervisor{};
    supervisor.evaluate({false, tca::FaultCode::InputRange}, tca::FaultCode::None, 100U);
    CHECK_TRUE(supervisor.request_reset(valid_frame(), {true, tca::FaultCode::None}));
    CHECK_EQ(supervisor.latched_fault(), tca::FaultCode::None);
    return true;
}

bool valid_application_cycle_selects_drive_gear() {
    tca::ControlApplication application{};
    auto frame = valid_frame();
    frame.direction_request = tca::DirectionRequest::Drive;
    frame.vehicle_speed_kph = 10.0;
    const auto output = application.step(frame, 100U, 900U);
    CHECK_EQ(output.mode, tca::OperatingMode::Normal);
    CHECK_EQ(output.selected_gear, tca::Gear::First);
    CHECK_EQ(output.torque_limit_pct, 100U);
    return true;
}

bool sensor_disagreement_forces_safe_output() {
    tca::ControlApplication application{};
    auto frame = valid_frame();
    frame.throttle_redundant_pct = 40.0;
    const auto output = application.step(frame, 100U, 900U);
    CHECK_EQ(output.mode, tca::OperatingMode::SafeState);
    CHECK_EQ(output.selected_gear, tca::Gear::Neutral);
    CHECK_EQ(output.torque_limit_pct, 0U);
    CHECK_TRUE(output.shift_inhibited);
    return true;
}

bool application_fault_remains_latched() {
    tca::ControlApplication application{};
    auto bad = valid_frame();
    bad.throttle_redundant_pct = 40.0;
    (void)application.step(bad, 100U, 900U);
    const auto output = application.step(valid_frame(), 100U, 900U);
    CHECK_EQ(output.mode, tca::OperatingMode::SafeState);
    return true;
}

bool application_reset_recovers_on_next_cycle() {
    tca::ControlApplication application{};
    auto bad = valid_frame();
    bad.throttle_redundant_pct = 40.0;
    (void)application.step(bad, 100U, 900U);
    const auto safe = valid_frame();
    CHECK_TRUE(application.request_fault_reset(safe, 100U));
    const auto output = application.step(safe, 100U, 900U);
    CHECK_EQ(output.mode, tca::OperatingMode::Normal);
    return true;
}

bool output_sequence_increments() {
    tca::ControlApplication application{};
    const auto first = application.step(valid_frame(), 100U, 900U);
    const auto second = application.step(valid_frame(), 100U, 900U);
    CHECK_EQ(second.sequence, first.sequence + 1U);
    return true;
}

bool output_crc_is_reproducible() {
    tca::ControlApplication first_application{};
    tca::ControlApplication second_application{};
    const auto first = first_application.step(valid_frame(), 100U, 900U);
    const auto second = second_application.step(valid_frame(), 100U, 900U);
    CHECK_EQ(first.integrity_crc, second.integrity_crc);
    return true;
}

bool illegal_direction_change_reaches_safe_state() {
    tca::ControlApplication application{};
    auto frame = valid_frame();
    frame.direction_request = tca::DirectionRequest::Drive;
    frame.vehicle_speed_kph = 25.0;
    (void)application.step(frame, 100U, 900U);
    frame.direction_request = tca::DirectionRequest::Reverse;
    const auto output = application.step(frame, 100U, 900U);
    CHECK_EQ(output.fault, tca::FaultCode::IllegalDirectionChange);
    CHECK_EQ(output.mode, tca::OperatingMode::SafeState);
    return true;
}

bool can_crc_accepts_valid_motion_frame() {
    const auto frame = tca::encode_motion_frame(valid_frame());
    CHECK_TRUE(tca::has_valid_can_crc(frame));
    return true;
}

bool can_rejects_bad_crc() {
    tca::CanInputAssembler assembler{};
    auto frame = tca::encode_motion_frame(valid_frame());
    frame.data[0U] ^= 0x01U;
    CHECK_EQ(assembler.ingest(frame, 100U).status, tca::CanIngestStatus::InvalidCrc);
    return true;
}

bool can_rejects_wrong_dlc() {
    tca::CanInputAssembler assembler{};
    auto frame = tca::encode_motion_frame(valid_frame());
    frame.dlc = 7U;
    CHECK_EQ(assembler.ingest(frame, 100U).status, tca::CanIngestStatus::InvalidLength);
    return true;
}

bool can_rejects_unknown_identifier() {
    tca::CanInputAssembler assembler{};
    auto frame = tca::encode_motion_frame(valid_frame());
    frame.id = 0x777U;
    CHECK_EQ(assembler.ingest(frame, 100U).status,
             tca::CanIngestStatus::UnknownIdentifier);
    return true;
}

bool can_decodes_paired_input_frames() {
    tca::CanInputAssembler assembler{};
    auto source = valid_frame();
    source.vehicle_speed_kph = 42.3;
    source.throttle_primary_pct = 31.5;
    source.direction_request = tca::DirectionRequest::Drive;
    CHECK_EQ(assembler.ingest(tca::encode_motion_frame(source), 120U).status,
             tca::CanIngestStatus::WaitingForPair);
    const auto result =
        assembler.ingest(tca::encode_driver_request_frame(source), 120U);
    CHECK_EQ(result.status, tca::CanIngestStatus::FrameReady);
    CHECK_TRUE(result.sensor_frame.has_value());
    CHECK_EQ(result.sensor_frame->sequence, source.sequence);
    CHECK_EQ(result.sensor_frame->vehicle_speed_kph, source.vehicle_speed_kph);
    CHECK_EQ(result.sensor_frame->throttle_primary_pct, source.throttle_primary_pct);
    CHECK_EQ(result.sensor_frame->direction_request, source.direction_request);
    return true;
}

bool can_pairs_frames_in_either_order() {
    tca::CanInputAssembler assembler{};
    const auto source = valid_frame();
    CHECK_EQ(assembler.ingest(tca::encode_driver_request_frame(source), 100U).status,
             tca::CanIngestStatus::WaitingForPair);
    const auto result = assembler.ingest(tca::encode_motion_frame(source), 100U);
    CHECK_EQ(result.status, tca::CanIngestStatus::FrameReady);
    CHECK_TRUE(result.sensor_frame.has_value());
    return true;
}

bool can_rejects_invalid_direction() {
    tca::CanInputAssembler assembler{};
    auto frame = tca::encode_driver_request_frame(valid_frame());
    frame.data[2U] = 9U;
    frame.data[7U] = 0U;
    frame.data[7U] = tca_crc8_sae_j1850(nullptr, 0U);
    CHECK_EQ(assembler.ingest(frame, 100U).status, tca::CanIngestStatus::InvalidCrc);

    frame = tca::encode_driver_request_frame(valid_frame());
    frame.data[2U] = 9U;
    const std::array<std::uint8_t, 10U> protected_bytes{
        static_cast<std::uint8_t>(frame.id & 0xFFU),
        static_cast<std::uint8_t>((frame.id >> 8U) & 0xFFU),
        frame.dlc,
        frame.data[0U],
        frame.data[1U],
        frame.data[2U],
        frame.data[3U],
        frame.data[4U],
        frame.data[5U],
        frame.data[6U],
    };
    frame.data[7U] =
        tca_crc8_sae_j1850(protected_bytes.data(), protected_bytes.size());
    CHECK_EQ(assembler.ingest(frame, 100U).status,
             tca::CanIngestStatus::InvalidSignal);
    return true;
}

bool can_detects_sequence_mismatch() {
    tca::CanInputAssembler assembler{};
    const auto first = valid_frame();
    auto second = valid_frame();
    second.sequence = 2U;
    CHECK_EQ(assembler.ingest(tca::encode_motion_frame(first), 100U).status,
             tca::CanIngestStatus::WaitingForPair);
    CHECK_EQ(assembler.ingest(tca::encode_driver_request_frame(second), 100U).status,
             tca::CanIngestStatus::SequenceMismatch);
    return true;
}

bool can_encodes_control_output() {
    tca::ControlOutput output{};
    output.sequence = 0x1234U;
    output.selected_gear = tca::Gear::Third;
    output.mode = tca::OperatingMode::Normal;
    output.torque_limit_pct = 85U;
    output.shift_inhibited = false;
    const auto frame = tca::encode_control_output_frame(output);
    CHECK_EQ(frame.id, tca::control_output_can_id);
    CHECK_EQ(frame.data[0U], static_cast<std::uint8_t>(tca::Gear::Third));
    CHECK_EQ(frame.data[3U], 85U);
    CHECK_EQ(frame.data[5U], 0x34U);
    CHECK_EQ(frame.data[6U], 0x12U);
    CHECK_TRUE(tca::has_valid_can_crc(frame));
    return true;
}

bool can_input_drives_control_cycle() {
    tca::CanInputAssembler assembler{};
    tca::ControlApplication application{};
    auto source = valid_frame();
    source.direction_request = tca::DirectionRequest::Drive;
    source.vehicle_speed_kph = 10.0;
    (void)assembler.ingest(tca::encode_motion_frame(source), 100U);
    const auto decoded =
        assembler.ingest(tca::encode_driver_request_frame(source), 100U);
    CHECK_TRUE(decoded.sensor_frame.has_value());
    const auto output = application.step(*decoded.sensor_frame, 100U, 900U);
    CHECK_EQ(output.selected_gear, tca::Gear::First);
    CHECK_TRUE(tca::has_valid_can_crc(tca::encode_control_output_frame(output)));
    return true;
}

struct TestCase {
    const char *name;
    bool (*run)();
};

constexpr std::array<TestCase, 47U> tests{{
    {"crc_empty_payload_is_defined", crc_empty_payload_is_defined},
    {"crc_rejects_null_non_empty_payload", crc_rejects_null_non_empty_payload},
    {"crc_is_deterministic", crc_is_deterministic},
    {"crc_changes_when_payload_changes", crc_changes_when_payload_changes},
    {"valid_inputs_are_accepted", valid_inputs_are_accepted},
    {"primary_throttle_range_is_checked", primary_throttle_range_is_checked},
    {"redundant_throttle_range_is_checked", redundant_throttle_range_is_checked},
    {"speed_range_is_checked", speed_range_is_checked},
    {"shaft_speed_range_is_checked", shaft_speed_range_is_checked},
    {"redundant_throttle_disagreement_is_detected", redundant_throttle_disagreement_is_detected},
    {"stale_input_is_detected", stale_input_is_detected},
    {"future_timestamp_does_not_underflow", future_timestamp_does_not_underflow},
    {"speed_limit_boundary_is_inclusive", speed_limit_boundary_is_inclusive},
    {"throttle_disagreement_boundary_is_inclusive", throttle_disagreement_boundary_is_inclusive},
    {"input_age_boundary_is_inclusive", input_age_boundary_is_inclusive},
    {"watchdog_budget_boundary_is_inclusive", watchdog_budget_boundary_is_inclusive},
    {"direction_change_speed_boundary_is_inclusive", direction_change_speed_boundary_is_inclusive},
    {"controller_starts_in_park", controller_starts_in_park},
    {"drive_request_selects_first_gear_at_low_speed", drive_request_selects_first_gear_at_low_speed},
    {"drive_schedule_upshifts_with_speed", drive_schedule_upshifts_with_speed},
    {"high_load_delays_upshift", high_load_delays_upshift},
    {"reverse_is_allowed_at_standstill", reverse_is_allowed_at_standstill},
    {"reverse_is_rejected_while_moving_forward", reverse_is_rejected_while_moving_forward},
    {"park_is_rejected_at_speed", park_is_rejected_at_speed},
    {"validation_fault_is_latched", validation_fault_is_latched},
    {"watchdog_overrun_is_latched", watchdog_overrun_is_latched},
    {"first_fault_is_preserved", first_fault_is_preserved},
    {"reset_is_rejected_while_moving", reset_is_rejected_while_moving},
    {"reset_requires_brake", reset_requires_brake},
    {"reset_is_accepted_at_safe_standstill", reset_is_accepted_at_safe_standstill},
    {"valid_application_cycle_selects_drive_gear", valid_application_cycle_selects_drive_gear},
    {"sensor_disagreement_forces_safe_output", sensor_disagreement_forces_safe_output},
    {"application_fault_remains_latched", application_fault_remains_latched},
    {"application_reset_recovers_on_next_cycle", application_reset_recovers_on_next_cycle},
    {"output_sequence_increments", output_sequence_increments},
    {"output_crc_is_reproducible", output_crc_is_reproducible},
    {"illegal_direction_change_reaches_safe_state", illegal_direction_change_reaches_safe_state},
    {"can_crc_accepts_valid_motion_frame", can_crc_accepts_valid_motion_frame},
    {"can_rejects_bad_crc", can_rejects_bad_crc},
    {"can_rejects_wrong_dlc", can_rejects_wrong_dlc},
    {"can_rejects_unknown_identifier", can_rejects_unknown_identifier},
    {"can_decodes_paired_input_frames", can_decodes_paired_input_frames},
    {"can_pairs_frames_in_either_order", can_pairs_frames_in_either_order},
    {"can_rejects_invalid_direction", can_rejects_invalid_direction},
    {"can_detects_sequence_mismatch", can_detects_sequence_mismatch},
    {"can_encodes_control_output", can_encodes_control_output},
    {"can_input_drives_control_cycle", can_input_drives_control_cycle},
}};

}  // namespace

int main() {
    std::size_t passed = 0U;
    for (const auto &test : tests) {
        if (test.run()) {
            ++passed;
            std::cout << "PASS " << test.name << '\n';
        } else {
            std::cout << "FAIL " << test.name << '\n';
        }
    }

    std::cout << passed << '/' << tests.size() << " tests passed\n";
    return passed == tests.size() ? 0 : 1;
}
