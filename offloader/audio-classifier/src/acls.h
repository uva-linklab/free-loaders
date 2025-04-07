#ifndef MDL_ACLS_H
#define MDL_ACLS_H

#include <stdint.h>

#include "acls-config.h"

extern uint16_t ACLS_SAMPLES[ACLS_SAMPLE_LEN];

/** Capture audio.
 */
void capture(void);

#define ACLS_RMSE_FRAME_SAMPLE_LEN ((uint32_t) 2048)
#define ACLS_RMSE_TOTAL_FRAMES ((uint32_t) ((ACLS_SAMPLE_LEN / ACLS_RMSE_FRAME_SAMPLE_LEN)) \
								+ (ACLS_SAMPLE_LEN % ACLS_RMSE_FRAME_SAMPLE_LEN == 0 ? 0 : 1))

/** Calculate RMSE statistics for audio samples.
 *
 * Records RMSE mean and stdev in `statistics_out`.
 */
void rmse_statistics(
	const uint16_t* const samples,
	float* const statistics_out);

/** Calculate centroid statistics for audio samples.
 *
 * Records centroid mean and stdev in `statistics_out`.
 */
void centroid_statistics(
	const uint16_t* const samples,
	float* statistics_out);

/** Calculate spectral bandwidth for audio samples.
 *
 *
 */
void spectral_bandwidth(
	const uint16_t* const samples,
	const float centroid_freq,
	float* const statistics_out);

/** Calculate MFCCs for audio samples.
 */
float* mfccs(
	const uint16_t* const samples);

#endif
