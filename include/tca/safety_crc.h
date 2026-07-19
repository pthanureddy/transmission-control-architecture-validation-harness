#ifndef TCA_SAFETY_CRC_H
#define TCA_SAFETY_CRC_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

uint8_t tca_crc8_sae_j1850(const uint8_t *data, size_t length);

#ifdef __cplusplus
}
#endif

#endif

