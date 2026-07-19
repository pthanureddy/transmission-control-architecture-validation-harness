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
    const std::array<tca::SensorFrame, 5U> drive_cycle{{
        {1U, 0U, 0.0, 800.0, 0.0, 0.0, 0.0, true, tca::DirectionRequest::Park},
        {2U, 10U, 8.0, 1500.0, 400.0, 18.0, 17.5, false, tca::DirectionRequest::Drive},
        {3U, 20U, 38.0, 2600.0, 1300.0, 28.0, 28.5, false, tca::DirectionRequest::Drive},
        {4U, 30U, 82.0, 3100.0, 2200.0, 22.0, 22.5, false, tca::DirectionRequest::Drive},
        {5U, 40U, 82.0, 3100.0, 2200.0, 22.0, 55.0, false, tca::DirectionRequest::Drive},
    }};

    std::cout << "cycle,input_sequence,gear,mode,fault,torque_limit,crc\n";
    for (std::size_t index = 0U; index < drive_cycle.size(); ++index) {
        const tca::ControlOutput output = application.step(
            drive_cycle[index], drive_cycle[index].timestamp_ms, 800U);
        std::cout << index << ',' << drive_cycle[index].sequence << ','
                  << gear_name(output.selected_gear) << ','
                  << static_cast<unsigned int>(output.mode) << ','
                  << static_cast<unsigned int>(output.fault) << ','
                  << static_cast<unsigned int>(output.torque_limit_pct) << ','
                  << static_cast<unsigned int>(output.integrity_crc) << '\n';
    }

    return 0;
}
