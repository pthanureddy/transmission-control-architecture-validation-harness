#pragma once

#include <cstdint>

namespace tca {

enum class DirectionRequest : std::uint8_t {
    Park = 0U,
    Neutral = 1U,
    Drive = 2U,
    Reverse = 3U,
};

enum class Gear : std::uint8_t {
    Park = 0U,
    Neutral = 1U,
    Reverse = 2U,
    First = 3U,
    Second = 4U,
    Third = 5U,
    Fourth = 6U,
    Fifth = 7U,
    Sixth = 8U,
};

enum class OperatingMode : std::uint8_t {
    Initializing = 0U,
    Normal = 1U,
    SafeState = 2U,
};

enum class FaultCode : std::uint8_t {
    None = 0U,
    InputRange = 1U,
    SensorDisagreement = 2U,
    StaleInput = 3U,
    IllegalDirectionChange = 4U,
    WatchdogOverrun = 5U,
};

struct SensorFrame {
    std::uint32_t sequence{0U};
    std::uint32_t timestamp_ms{0U};
    double vehicle_speed_kph{0.0};
    double input_shaft_rpm{0.0};
    double output_shaft_rpm{0.0};
    double throttle_primary_pct{0.0};
    double throttle_redundant_pct{0.0};
    bool brake_applied{true};
    DirectionRequest direction_request{DirectionRequest::Park};
};

struct ValidationResult {
    bool valid{true};
    FaultCode fault{FaultCode::None};
};

struct ControlOutput {
    std::uint32_t sequence{0U};
    Gear selected_gear{Gear::Park};
    OperatingMode mode{OperatingMode::Initializing};
    FaultCode fault{FaultCode::None};
    std::uint8_t torque_limit_pct{0U};
    bool shift_inhibited{true};
    std::uint8_t integrity_crc{0U};
};

struct QualityLimits {
    double maximum_speed_kph{260.0};
    double maximum_shaft_rpm{12000.0};
    double maximum_throttle_disagreement_pct{5.0};
    std::uint32_t maximum_input_age_ms{100U};
    std::uint32_t control_cycle_budget_us{5000U};
    double direction_change_speed_limit_kph{1.0};
};

}  // namespace tca

