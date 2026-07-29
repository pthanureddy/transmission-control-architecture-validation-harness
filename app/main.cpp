#include "tca/can_protocol.hpp"
#include "tca/control_application.hpp"

#include <array>
#include <cstdint>
#include <iostream>

namespace {

const char *gear_name(const tca::Gear gear) {
    switch (gear) {
        case tca::Gear::Park: return "P";
        case tca::Gear::Neutral: return "N";
        case tca::Gear::Reverse: return "R";
        case tca::Gear::First: return "1";
        case tca::Gear::Second: return "2";
        case tca::Gear::Third: return "3";
        case tca::Gear::Fourth: return "4";
        case tca::Gear::Fifth: return "5";
        case tca::Gear::Sixth: return "6";
    }
    return "?";
}

}  // namespace

int main() {
    tca::ControlApplication application{};
    tca::CanInputAssembler can_input{};
    const std::array<tca::SensorFrame, 5U> drive_cycle{{
        {1U, 0U, 0.0, 800.0, 0.0, 0.0, 0.0, true, tca::DirectionRequest::Park},
        {2U, 10U, 8.0, 1500.0, 400.0, 18.0, 17.5, false, tca::DirectionRequest::Drive},
        {3U, 20U, 38.0, 2600.0, 1300.0, 28.0, 28.5, false, tca::DirectionRequest::Drive},
        {4U, 30U, 82.0, 3100.0, 2200.0, 22.0, 22.5, false, tca::DirectionRequest::Drive},
        {5U, 40U, 82.0, 3100.0, 2200.0, 22.0, 55.0, false, tca::DirectionRequest::Drive},
    }};

    std::cout << "cycle,input_sequence,gear,mode,fault,torque_limit,can_crc\n";
    for (std::size_t index = 0U; index < drive_cycle.size(); ++index) {
        const auto motion_result =
            can_input.ingest(tca::encode_motion_frame(drive_cycle[index]),
                             drive_cycle[index].timestamp_ms);
        if (motion_result.status != tca::CanIngestStatus::WaitingForPair) {
            return 1;
        }
        const auto driver_result =
            can_input.ingest(tca::encode_driver_request_frame(drive_cycle[index]),
                             drive_cycle[index].timestamp_ms);
        if (!driver_result.sensor_frame.has_value()) {
            return 1;
        }
        const tca::ControlOutput output =
            application.step(*driver_result.sensor_frame,
                             drive_cycle[index].timestamp_ms,
                             800U);
        const tca::CanFrame output_frame = tca::encode_control_output_frame(output);
        std::cout << index << ',' << drive_cycle[index].sequence << ','
                  << gear_name(output.selected_gear) << ','
                  << static_cast<unsigned int>(output.mode) << ','
                  << static_cast<unsigned int>(output.fault) << ','
                  << static_cast<unsigned int>(output.torque_limit_pct) << ','
                  << static_cast<unsigned int>(output_frame.data[7U]) << '\n';
    }

    return 0;
}
