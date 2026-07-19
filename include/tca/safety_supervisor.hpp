#pragma once

#include "tca/types.hpp"

namespace tca {

class SafetySupervisor final {
public:
    explicit SafetySupervisor(QualityLimits limits = {});

    void evaluate(const ValidationResult &validation,
                  FaultCode architecture_fault,
                  std::uint32_t execution_time_us) noexcept;

    [[nodiscard]] bool request_reset(const SensorFrame &frame,
                                     const ValidationResult &validation) noexcept;

    [[nodiscard]] OperatingMode mode() const noexcept;
    [[nodiscard]] FaultCode latched_fault() const noexcept;

private:
    void latch(FaultCode fault) noexcept;

    QualityLimits limits_;
    OperatingMode mode_{OperatingMode::Initializing};
    FaultCode latched_fault_{FaultCode::None};
};

}  // namespace tca

