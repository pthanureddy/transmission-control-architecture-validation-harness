#ifndef TCA_SIL_API_H
#define TCA_SIL_API_H

#include <stdint.h>

#if defined(_WIN32)
#if defined(TCA_SIL_BUILD)
#define TCA_SIL_API __declspec(dllexport)
#else
#define TCA_SIL_API __declspec(dllimport)
#endif
#else
#define TCA_SIL_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct tca_sil_session tca_sil_session;

/* Fixed-width result record shared with Python ctypes. */
typedef struct tca_sil_result {
    uint32_t output_sequence;
    uint16_t output_can_id;
    uint8_t ingest_status;
    uint8_t has_output;
    uint8_t output_dlc;
    uint8_t output_data[8];
    uint8_t selected_gear;
    uint8_t operating_mode;
    uint8_t fault_code;
    uint8_t torque_limit_pct;
    uint8_t shift_inhibited;
} tca_sil_result;

TCA_SIL_API uint32_t tca_sil_abi_version(void);
TCA_SIL_API tca_sil_session *tca_sil_create(void);
TCA_SIL_API void tca_sil_destroy(tca_sil_session *session);
TCA_SIL_API int32_t tca_sil_reset(tca_sil_session *session);

/*
 * Feeds one repository-defined, synthetic CAN frame to the compiled DUT.
 * reception_timestamp_ms becomes the assembled input timestamp; now_ms lets
 * tests exercise input-age handling without wall-clock sleeps.
 */
TCA_SIL_API int32_t tca_sil_ingest(tca_sil_session *session,
                                   uint16_t can_id,
                                   uint8_t dlc,
                                   const uint8_t data[8],
                                   uint32_t reception_timestamp_ms,
                                   uint32_t now_ms,
                                   uint32_t execution_time_us,
                                   tca_sil_result *result);

#ifdef __cplusplus
}
#endif

#endif
