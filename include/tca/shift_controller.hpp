#pragma once

#include "tca/types.hpp"

namespace tca {

struct ShiftDecision {
    Gear gear{Gear::Park};
    FaultCode fault{FaultCode::None};
};

class ShiftController final {
public:
    explicit ShiftController(QualityLimits limits = {});

    [[nodiscard]] ShiftDecision update(const SensorFrame &frame) noexcept;
    [[nodiscard]] Gear current_gear() const noexcept;
    void force_safe_state() noexcept;

private:
    [[nodiscard]] static Gear scheduled_drive_gear(double vehicle_speed_kph,
                                                   double throttle_pct) noexcept;
    [[nodiscard]] bool direction_change_is_legal(DirectionRequest request,
                                                 double speed_kph) const noexcept;

    QualityLimits limits_;
    Gear current_gear_{Gear::Park};
    DirectionRequest current_direction_{DirectionRequest::Park};
};

}  // namespace tca

