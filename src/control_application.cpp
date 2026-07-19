#include "tca/control_application.hpp"

#include "tca/safety_crc.h"

#include <array>

namespace tca {

ControlApplication::ControlApplication(QualityLimits limits)
    : monitor_(limits), shift_controller_(limits), supervisor_(limits) {}

ControlOutput ControlApplication::step(const SensorFrame &frame,
                                       const std::uint32_t now_ms,
                                       const std::uint32_t execution_time_us) noexcept {
    const ValidationResult validation = monitor_.validate(frame, now_ms);
    ShiftDecision decision{shift_controller_.current_gear(), FaultCode::None};
    if (validation.valid) {
        decision = shift_controller_.update(frame);
    }

    supervisor_.evaluate(validation, decision.fault, execution_time_us);

    ControlOutput output{};
    output.sequence = ++output_sequence_;
    output.mode = supervisor_.mode();
    output.fault = supervisor_.latched_fault();

    if (output.mode == OperatingMode::SafeState) {
        shift_controller_.force_safe_state();
        output.selected_gear = Gear::Neutral;
        output.torque_limit_pct = 0U;
        output.shift_inhibited = true;
    } else {
        output.selected_gear = decision.gear;
        output.torque_limit_pct = 100U;
        output.shift_inhibited = false;
    }

    output.integrity_crc = calculate_output_crc(output);
    return output;
}

bool ControlApplication::request_fault_reset(const SensorFrame &frame,
                                             const std::uint32_t now_ms) noexcept {
    const ValidationResult validation = monitor_.validate(frame, now_ms);
    return supervisor_.request_reset(frame, validation);
}

std::uint8_t ControlApplication::calculate_output_crc(const ControlOutput &output) noexcept {
    const std::array<std::uint8_t, 8U> payload{
        static_cast<std::uint8_t>(output.sequence & 0xFFU),
        static_cast<std::uint8_t>((output.sequence >> 8U) & 0xFFU),
        static_cast<std::uint8_t>((output.sequence >> 16U) & 0xFFU),
        static_cast<std::uint8_t>((output.sequence >> 24U) & 0xFFU),
        static_cast<std::uint8_t>(output.selected_gear),
        static_cast<std::uint8_t>(output.mode),
        static_cast<std::uint8_t>(output.fault),
        output.torque_limit_pct,
    };
    return tca_crc8_sae_j1850(payload.data(), payload.size());
}

}  // namespace tca

