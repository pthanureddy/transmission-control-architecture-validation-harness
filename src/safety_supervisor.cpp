#include "tca/safety_supervisor.hpp"

namespace tca {

SafetySupervisor::SafetySupervisor(QualityLimits limits) : limits_(limits) {}

void SafetySupervisor::evaluate(const ValidationResult &validation,
                                const FaultCode architecture_fault,
                                const std::uint32_t execution_time_us) noexcept {
    if (!validation.valid) {
        latch(validation.fault);
        return;
    }

    if (architecture_fault != FaultCode::None) {
        latch(architecture_fault);
        return;
    }

    if (execution_time_us > limits_.control_cycle_budget_us) {
        latch(FaultCode::WatchdogOverrun);
        return;
    }

    if (latched_fault_ == FaultCode::None) {
        mode_ = OperatingMode::Normal;
    }
}

bool SafetySupervisor::request_reset(const SensorFrame &frame,
                                     const ValidationResult &validation) noexcept {
    const bool stationary = frame.vehicle_speed_kph <= limits_.direction_change_speed_limit_kph;
    if (!stationary || !frame.brake_applied || !validation.valid) {
        return false;
    }

    latched_fault_ = FaultCode::None;
    mode_ = OperatingMode::Initializing;
    return true;
}

OperatingMode SafetySupervisor::mode() const noexcept {
    return mode_;
}

FaultCode SafetySupervisor::latched_fault() const noexcept {
    return latched_fault_;
}

void SafetySupervisor::latch(const FaultCode fault) noexcept {
    if (latched_fault_ == FaultCode::None) {
        latched_fault_ = fault;
    }
    mode_ = OperatingMode::SafeState;
}

}  // namespace tca

