#include "tca/can_protocol.hpp"
#include "tca/sil_api.h"

#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>

namespace {

bool ingest(tca_sil_session *session,
            const tca::CanFrame &frame,
            const std::uint32_t reception_ms,
            const std::uint32_t now_ms,
            tca_sil_result &result) {
    return tca_sil_ingest(session,
                          frame.id,
                          frame.dlc,
                          frame.data.data(),
                          reception_ms,
                          now_ms,
                          800U,
                          &result) == 0;
}

}  // namespace

int main() {
    if (tca_sil_abi_version() != 1U) {
        std::cerr << "Unexpected SIL ABI version\n";
        return 1;
    }

    tca_sil_session *session = tca_sil_create();
    if (session == nullptr) {
        std::cerr << "Could not create SIL session\n";
        return 1;
    }

    const tca::SensorFrame input{
        7U, 40U, 25.0, 2200.0, 900.0, 30.0, 30.5, false,
        tca::DirectionRequest::Drive};
    const tca::CanFrame motion = tca::encode_motion_frame(input);
    const tca::CanFrame driver = tca::encode_driver_request_frame(input);
    tca_sil_result result{};

    if (!ingest(session, motion, 40U, 40U, result) ||
        result.ingest_status !=
            static_cast<std::uint8_t>(tca::CanIngestStatus::WaitingForPair) ||
        result.has_output != 0U) {
        std::cerr << "Motion-frame contract failed\n";
        tca_sil_destroy(session);
        return 1;
    }
    if (!ingest(session, driver, 40U, 40U, result) ||
        result.ingest_status !=
            static_cast<std::uint8_t>(tca::CanIngestStatus::FrameReady) ||
        result.has_output != 1U || result.output_can_id != tca::control_output_can_id ||
        result.output_dlc != tca::can_payload_length) {
        std::cerr << "Paired-frame contract failed\n";
        tca_sil_destroy(session);
        return 1;
    }

    tca::CanFrame corrupt = motion;
    corrupt.data[0U] ^= 0x01U;
    if (!ingest(session, corrupt, 50U, 50U, result) ||
        result.ingest_status !=
            static_cast<std::uint8_t>(tca::CanIngestStatus::InvalidCrc) ||
        result.has_output != 0U) {
        std::cerr << "Corrupt-frame contract failed\n";
        tca_sil_destroy(session);
        return 1;
    }

    if (tca_sil_reset(session) != 0) {
        std::cerr << "Reset contract failed\n";
        tca_sil_destroy(session);
        return 1;
    }

    tca_sil_destroy(session);
    std::cout << "SIL bridge contract passed\n";
    return 0;
}
