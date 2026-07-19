#pragma once

#include "tca/types.hpp"

namespace tca {

class PlausibilityMonitor final {
public:
    explicit PlausibilityMonitor(QualityLimits limits = {});

    [[nodiscard]] ValidationResult validate(const SensorFrame &frame,
                                            std::uint32_t now_ms) const noexcept;

private:
    QualityLimits limits_;
};

}  // namespace tca

