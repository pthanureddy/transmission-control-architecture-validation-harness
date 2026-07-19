#include "tca/shift_controller.hpp"

namespace tca {

ShiftController::ShiftController(QualityLimits limits) : limits_(limits) {}

ShiftDecision ShiftController::update(const SensorFrame &frame) noexcept {
    if (!direction_change_is_legal(frame.direction_request, frame.vehicle_speed_kph)) {
        return {current_gear_, FaultCode::IllegalDirectionChange};
    }

    current_direction_ = frame.direction_request;
    switch (frame.direction_request) {
        case DirectionRequest::Park:
            current_gear_ = Gear::Park;
            break;
        case DirectionRequest::Neutral:
            current_gear_ = Gear::Neutral;
            break;
        case DirectionRequest::Reverse:
            current_gear_ = Gear::Reverse;
            break;
        case DirectionRequest::Drive:
            current_gear_ = scheduled_drive_gear(frame.vehicle_speed_kph,
                                                 frame.throttle_primary_pct);
            break;
    }

    return {current_gear_, FaultCode::None};
}

Gear ShiftController::current_gear() const noexcept {
    return current_gear_;
}

void ShiftController::force_safe_state() noexcept {
    current_gear_ = Gear::Neutral;
    current_direction_ = DirectionRequest::Neutral;
}

Gear ShiftController::scheduled_drive_gear(const double vehicle_speed_kph,
                                           const double throttle_pct) noexcept {
    const double load_offset = throttle_pct >= 70.0 ? 12.0 : (throttle_pct >= 35.0 ? 6.0 : 0.0);

    if (vehicle_speed_kph < 15.0 + load_offset) {
        return Gear::First;
    }
    if (vehicle_speed_kph < 30.0 + load_offset) {
        return Gear::Second;
    }
    if (vehicle_speed_kph < 50.0 + load_offset) {
        return Gear::Third;
    }
    if (vehicle_speed_kph < 75.0 + load_offset) {
        return Gear::Fourth;
    }
    if (vehicle_speed_kph < 105.0 + load_offset) {
        return Gear::Fifth;
    }
    return Gear::Sixth;
}

bool ShiftController::direction_change_is_legal(const DirectionRequest request,
                                                const double speed_kph) const noexcept {
    if (request == current_direction_) {
        return true;
    }

    if (speed_kph <= limits_.direction_change_speed_limit_kph) {
        return true;
    }

    const bool entering_non_drive = request == DirectionRequest::Reverse ||
                                    request == DirectionRequest::Park;
    const bool leaving_reverse = current_direction_ == DirectionRequest::Reverse &&
                                 request == DirectionRequest::Drive;
    return !entering_non_drive && !leaving_reverse;
}

}  // namespace tca

