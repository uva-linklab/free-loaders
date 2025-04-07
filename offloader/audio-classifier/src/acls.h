#ifndef MDL_ACLS_H
#define MDL_ACLS_H

#include <stdint.h>

#include "acls-config.h"

/** Perform setup checks and initialization.
 */
void check_initialize(void);

/** Capture audio.
 */
void capture(
	uint16_t* const sample_buffer);

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
