#ifndef MDL_ACLS_H
#define MDL_ACLS_H

#include <stdint.h>

/** Calculate RMSE statistics for audio samples.
 *
 * Records RMSE mean and stdev in `statistics_out`.
 */
void rmse_statistics(
	const uint16_t* const samples,
	float* statistics_out);

/** Calculate centroid statistics for audio samples.
 *
 * Records centroid mean and stdev in `statistics_out`.
 */
void centroid_statistics(
	const uint16_t* const samples,
	float* statistics_out);

/** Calculate MFCC statistics for audio samples.
 *
 * Records the mean and stdev for each MFCC in `statistics_out`.
 */
void mfcc_statistics(
	const uint16_t* const samples,
	float* statistics_out);

#endif
