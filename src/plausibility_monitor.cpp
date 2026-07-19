#include "tca/plausibility_monitor.hpp"

#include <cmath>

namespace tca {

PlausibilityMonitor::PlausibilityMonitor(QualityLimits limits) : limits_(limits) {}

ValidationResult PlausibilityMonitor::validate(const SensorFrame &frame,
                                                const std::uint32_t now_ms) const noexcept {
    const bool throttle_out_of_range = frame.throttle_primary_pct < 0.0 ||
                                       frame.throttle_primary_pct > 100.0 ||
                                       frame.throttle_redundant_pct < 0.0 ||
                                       frame.throttle_redundant_pct > 100.0;
    const bool speed_out_of_range = frame.vehicle_speed_kph < 0.0 ||
                                    frame.vehicle_speed_kph > limits_.maximum_speed_kph;
    const bool rpm_out_of_range = frame.input_shaft_rpm < 0.0 ||
                                  frame.input_shaft_rpm > limits_.maximum_shaft_rpm ||
                                  frame.output_shaft_rpm < 0.0 ||
                                  frame.output_shaft_rpm > limits_.maximum_shaft_rpm;

    if (throttle_out_of_range || speed_out_of_range || rpm_out_of_range) {
        return {false, FaultCode::InputRange};
    }

    if (std::abs(frame.throttle_primary_pct - frame.throttle_redundant_pct) >
        limits_.maximum_throttle_disagreement_pct) {
        return {false, FaultCode::SensorDisagreement};
    }

    const std::uint32_t age_ms = now_ms >= frame.timestamp_ms
                                     ? now_ms - frame.timestamp_ms
                                     : 0U;
    if (age_ms > limits_.maximum_input_age_ms) {
        return {false, FaultCode::StaleInput};
    }

    return {true, FaultCode::None};
}

}  // namespace tca

