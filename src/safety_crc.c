#include "tca/safety_crc.h"

uint8_t tca_crc8_sae_j1850(const uint8_t *data, size_t length) {
    uint8_t crc = 0xFFU;

    if ((data == NULL) && (length != 0U)) {
        return 0U;
    }

    for (size_t index = 0U; index < length; ++index) {
        crc ^= data[index];
        for (uint8_t bit = 0U; bit < 8U; ++bit) {
            if ((crc & 0x80U) != 0U) {
                crc = (uint8_t)((uint8_t)(crc << 1U) ^ 0x1DU);
            } else {
                crc = (uint8_t)(crc << 1U);
            }
        }
    }

    return (uint8_t)(crc ^ 0xFFU);
}

