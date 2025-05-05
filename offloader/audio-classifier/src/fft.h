#ifndef MDL_FFT_H
#define MDL_FFT_H

#include <stdint.h>

#include "acls-config.h"

#define FFT_OUT_SIZE 512

void fft(
	const uint16_t* const samples,
	const uint32_t samples_len,
	float* const out_real,
	float* const out_imag);

/** Compute the power spectrum of the FFT.
 *
 * Places the result in out_psd.
 * It is possible to alias out_real or out_imag to out_psd.
 */
void psd(
	const float* const real,
	const float* const imag,
	float* const out_psd,
	const uint32_t arr_len);

#endif
