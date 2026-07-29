#pragma once

#include "tca/types.hpp"

#include <array>
#include <cstdint>
#include <optional>

namespace tca {

inline constexpr std::uint16_t motion_can_id{0x180U};
inline constexpr std::uint16_t driver_request_can_id{0x181U};
inline constexpr std::uint16_t control_output_can_id{0x280U};
inline constexpr std::uint8_t can_payload_length{8U};

struct CanFrame {
    std::uint16_t id{0U};
    std::uint8_t dlc{0U};
    std::array<std::uint8_t, 8U> data{};
};

enum class CanIngestStatus : std::uint8_t {
    WaitingForPair = 0U,
    FrameReady = 1U,
    UnknownIdentifier = 2U,
    InvalidLength = 3U,
    InvalidCrc = 4U,
    InvalidSignal = 5U,
    SequenceMismatch = 6U,
};

struct CanIngestResult {
    CanIngestStatus status{CanIngestStatus::WaitingForPair};
    std::optional<SensorFrame> sensor_frame{};
};

[[nodiscard]] bool has_valid_can_crc(const CanFrame &frame) noexcept;
[[nodiscard]] CanFrame encode_motion_frame(const SensorFrame &frame) noexcept;
[[nodiscard]] CanFrame encode_driver_request_frame(const SensorFrame &frame) noexcept;
[[nodiscard]] CanFrame encode_control_output_frame(const ControlOutput &output) noexcept;

class CanInputAssembler final {
public:
    [[nodiscard]] CanIngestResult ingest(const CanFrame &frame,
                                         std::uint32_t reception_timestamp_ms) noexcept;

private:
    struct MotionSignals {
        std::uint8_t sequence{0U};
        double vehicle_speed_kph{0.0};
        double input_shaft_rpm{0.0};
        double output_shaft_rpm{0.0};
    };

    struct DriverSignals {
        std::uint8_t sequence{0U};
        double throttle_primary_pct{0.0};
        double throttle_redundant_pct{0.0};
        bool brake_applied{false};
        DirectionRequest direction_request{DirectionRequest::Park};
    };

    [[nodiscard]] CanIngestResult try_assemble(
        std::uint32_t reception_timestamp_ms) noexcept;

    std::optional<MotionSignals> motion_{};
    std::optional<DriverSignals> driver_{};
};

}  // namespace tca
