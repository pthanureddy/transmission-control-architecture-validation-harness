#include "tca/can_protocol.hpp"

#include "tca/safety_crc.h"

#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>

namespace tca {
namespace {

constexpr std::size_t crc_index{7U};

std::uint8_t calculate_can_crc(const CanFrame &frame) noexcept {
    const std::array<std::uint8_t, 10U> protected_bytes{
        static_cast<std::uint8_t>(frame.id & 0xFFU),
        static_cast<std::uint8_t>((frame.id >> 8U) & 0xFFU),
        frame.dlc,
        frame.data[0U],
        frame.data[1U],
        frame.data[2U],
        frame.data[3U],
        frame.data[4U],
        frame.data[5U],
        frame.data[6U],
    };
    return tca_crc8_sae_j1850(protected_bytes.data(), protected_bytes.size());
}

std::uint16_t pack_scaled_u16(const double value, const double scale) noexcept {
    if (value <= 0.0) {
        return 0U;
    }
    const double scaled = value * scale;
    if (scaled >= static_cast<double>(std::numeric_limits<std::uint16_t>::max())) {
        return std::numeric_limits<std::uint16_t>::max();
    }
    return static_cast<std::uint16_t>(std::lround(scaled));
}

std::uint8_t pack_throttle(const double value) noexcept {
    if (value <= 0.0) {
        return 0U;
    }
    if (value >= 100.0) {
        return 200U;
    }
    return static_cast<std::uint8_t>(std::lround(value * 2.0));
}

void write_u16(std::array<std::uint8_t, 8U> &data,
               const std::size_t offset,
               const std::uint16_t value) noexcept {
    data[offset] = static_cast<std::uint8_t>(value & 0xFFU);
    data[offset + 1U] = static_cast<std::uint8_t>((value >> 8U) & 0xFFU);
}

std::uint16_t read_u16(const std::array<std::uint8_t, 8U> &data,
                       const std::size_t offset) noexcept {
    const std::uint16_t low = data[offset];
    const std::uint16_t high = data[offset + 1U];
    return static_cast<std::uint16_t>(low | static_cast<std::uint16_t>(high << 8U));
}

void finalize_crc(CanFrame &frame) noexcept {
    frame.data[crc_index] = calculate_can_crc(frame);
}

}  // namespace

bool has_valid_can_crc(const CanFrame &frame) noexcept {
    return frame.dlc == can_payload_length &&
           frame.data[crc_index] == calculate_can_crc(frame);
}

CanFrame encode_motion_frame(const SensorFrame &frame) noexcept {
    CanFrame encoded{motion_can_id, can_payload_length, {}};
    write_u16(encoded.data, 0U, pack_scaled_u16(frame.vehicle_speed_kph, 10.0));
    write_u16(encoded.data, 2U, pack_scaled_u16(frame.input_shaft_rpm, 1.0));
    write_u16(encoded.data, 4U, pack_scaled_u16(frame.output_shaft_rpm, 1.0));
    encoded.data[6U] = static_cast<std::uint8_t>(frame.sequence & 0xFFU);
    finalize_crc(encoded);
    return encoded;
}

CanFrame encode_driver_request_frame(const SensorFrame &frame) noexcept {
    CanFrame encoded{driver_request_can_id, can_payload_length, {}};
    encoded.data[0U] = pack_throttle(frame.throttle_primary_pct);
    encoded.data[1U] = pack_throttle(frame.throttle_redundant_pct);
    encoded.data[2U] = static_cast<std::uint8_t>(frame.direction_request);
    encoded.data[3U] = frame.brake_applied ? 1U : 0U;
    encoded.data[6U] = static_cast<std::uint8_t>(frame.sequence & 0xFFU);
    finalize_crc(encoded);
    return encoded;
}

CanFrame encode_control_output_frame(const ControlOutput &output) noexcept {
    CanFrame encoded{control_output_can_id, can_payload_length, {}};
    encoded.data[0U] = static_cast<std::uint8_t>(output.selected_gear);
    encoded.data[1U] = static_cast<std::uint8_t>(output.mode);
    encoded.data[2U] = static_cast<std::uint8_t>(output.fault);
    encoded.data[3U] = output.torque_limit_pct;
    encoded.data[4U] = output.shift_inhibited ? 1U : 0U;
    write_u16(encoded.data, 5U, static_cast<std::uint16_t>(output.sequence & 0xFFFFU));
    finalize_crc(encoded);
    return encoded;
}

CanIngestResult CanInputAssembler::ingest(
    const CanFrame &frame,
    const std::uint32_t reception_timestamp_ms) noexcept {
    if (frame.id != motion_can_id && frame.id != driver_request_can_id) {
        return {CanIngestStatus::UnknownIdentifier, std::nullopt};
    }
    if (frame.dlc != can_payload_length) {
        return {CanIngestStatus::InvalidLength, std::nullopt};
    }
    if (!has_valid_can_crc(frame)) {
        return {CanIngestStatus::InvalidCrc, std::nullopt};
    }

    if (frame.id == motion_can_id) {
        motion_ = MotionSignals{
            frame.data[6U],
            static_cast<double>(read_u16(frame.data, 0U)) / 10.0,
            static_cast<double>(read_u16(frame.data, 2U)),
            static_cast<double>(read_u16(frame.data, 4U)),
        };
    } else {
        const std::uint8_t direction = frame.data[2U];
        if (direction > static_cast<std::uint8_t>(DirectionRequest::Reverse)) {
            return {CanIngestStatus::InvalidSignal, std::nullopt};
        }
        driver_ = DriverSignals{
            frame.data[6U],
            static_cast<double>(frame.data[0U]) / 2.0,
            static_cast<double>(frame.data[1U]) / 2.0,
            (frame.data[3U] & 0x01U) != 0U,
            static_cast<DirectionRequest>(direction),
        };
    }

    return try_assemble(reception_timestamp_ms);
}

CanIngestResult CanInputAssembler::try_assemble(
    const std::uint32_t reception_timestamp_ms) noexcept {
    if (!motion_.has_value() || !driver_.has_value()) {
        return {CanIngestStatus::WaitingForPair, std::nullopt};
    }
    if (motion_->sequence != driver_->sequence) {
        return {CanIngestStatus::SequenceMismatch, std::nullopt};
    }

    SensorFrame frame{};
    frame.sequence = motion_->sequence;
    frame.timestamp_ms = reception_timestamp_ms;
    frame.vehicle_speed_kph = motion_->vehicle_speed_kph;
    frame.input_shaft_rpm = motion_->input_shaft_rpm;
    frame.output_shaft_rpm = motion_->output_shaft_rpm;
    frame.throttle_primary_pct = driver_->throttle_primary_pct;
    frame.throttle_redundant_pct = driver_->throttle_redundant_pct;
    frame.brake_applied = driver_->brake_applied;
    frame.direction_request = driver_->direction_request;

    motion_.reset();
    driver_.reset();
    return {CanIngestStatus::FrameReady, frame};
}

}  // namespace tca
