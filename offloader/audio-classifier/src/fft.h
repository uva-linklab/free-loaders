#ifndef MDL_FFT_H
#define MDL_FFT_H

#include <stdint.h>

#include "acls-config.h"

#define FFT_OUT_LEN (ACLS_SAMPLE_LEN)

extern float __fft_out_real[ACLS_SAMPLE_LEN];
extern float __fft_out_imag[ACLS_SAMPLE_LEN];

inline const float* fft_result_real(void) { return __fft_out_real; }
inline const float* fft_result_imag(void) { return __fft_out_imag; }

void fft(
	const uint16_t* const samples,
	const uint16_t samples_len);

/** Compute the power spectrum of the FFT.
 */
void psd(void);

#endif
