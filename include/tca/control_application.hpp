#pragma once

#include "tca/plausibility_monitor.hpp"
#include "tca/safety_supervisor.hpp"
#include "tca/shift_controller.hpp"

namespace tca {

class ControlApplication final {
public:
    explicit ControlApplication(QualityLimits limits = {});

    [[nodiscard]] ControlOutput step(const SensorFrame &frame,
                                     std::uint32_t now_ms,
                                     std::uint32_t execution_time_us) noexcept;

    [[nodiscard]] bool request_fault_reset(const SensorFrame &frame,
                                           std::uint32_t now_ms) noexcept;

private:
    [[nodiscard]] static std::uint8_t calculate_output_crc(const ControlOutput &output) noexcept;

    PlausibilityMonitor monitor_;
    ShiftController shift_controller_;
    SafetySupervisor supervisor_;
    std::uint32_t output_sequence_{0U};
};

}  // namespace tca

