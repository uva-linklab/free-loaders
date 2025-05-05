#ifndef MDL_ACLS_H
#define MDL_ACLS_H

#include <stdint.h>

#include "acls-config.h"

/** Perform setup checks and initialization.
 */
void check_initialize(void);

/** Perform audio event classification.
 */
void classify(
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
	const float* const fdm,
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
 *
 * Either fdm_real or fdm_imag can be aliased to psd_scratch.
 * The contents of psd_scratch will be overwritten.
 */
float* mfccs(
	const float* const samples,
	float* const fdm_real,
	float* const fdm_imag,
	float* const psd_scratch);

#endif
