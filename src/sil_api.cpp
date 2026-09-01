#include "tca/sil_api.h"

#include "tca/can_protocol.hpp"
#include "tca/control_application.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <new>

struct tca_sil_session {
    tca::CanInputAssembler can_input{};
    tca::ControlApplication application{};
};

namespace {

void clear_result(tca_sil_result &result) noexcept {
    result = {};
}

}  // namespace

extern "C" {

uint32_t tca_sil_abi_version(void) {
    return 1U;
}

tca_sil_session *tca_sil_create(void) {
    return new (std::nothrow) tca_sil_session{};
}

void tca_sil_destroy(tca_sil_session *session) {
    delete session;
}

int32_t tca_sil_reset(tca_sil_session *session) {
    if (session == nullptr) {
        return -1;
    }
    session->can_input = tca::CanInputAssembler{};
    session->application = tca::ControlApplication{};
    return 0;
}

int32_t tca_sil_ingest(tca_sil_session *session,
                       const uint16_t can_id,
                       const uint8_t dlc,
                       const uint8_t data[8],
                       const uint32_t reception_timestamp_ms,
                       const uint32_t now_ms,
                       const uint32_t execution_time_us,
                       tca_sil_result *result) {
    if (session == nullptr || data == nullptr || result == nullptr) {
        return -1;
    }

    clear_result(*result);
    tca::CanFrame frame{};
    frame.id = can_id;
    frame.dlc = dlc;
    std::copy_n(data, frame.data.size(), frame.data.begin());

    const tca::CanIngestResult ingest =
        session->can_input.ingest(frame, reception_timestamp_ms);
    result->ingest_status = static_cast<uint8_t>(ingest.status);
    if (!ingest.sensor_frame.has_value()) {
        return 0;
    }

    const tca::ControlOutput output = session->application.step(
        *ingest.sensor_frame, now_ms, execution_time_us);
    const tca::CanFrame output_frame = tca::encode_control_output_frame(output);

    result->has_output = 1U;
    result->output_sequence = output.sequence;
    result->output_can_id = output_frame.id;
    result->output_dlc = output_frame.dlc;
    std::copy(output_frame.data.begin(), output_frame.data.end(), result->output_data);
    result->selected_gear = static_cast<uint8_t>(output.selected_gear);
    result->operating_mode = static_cast<uint8_t>(output.mode);
    result->fault_code = static_cast<uint8_t>(output.fault);
    result->torque_limit_pct = output.torque_limit_pct;
    result->shift_inhibited = output.shift_inhibited ? 1U : 0U;
    return 0;
}

}  // extern "C"
