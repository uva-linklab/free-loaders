#include "fft.h"

#include <math.h>

float __fft_out_real[ACLS_SAMPLE_LEN];
float __fft_out_imag[ACLS_SAMPLE_LEN];

// Function to perform bit reversal of an index
static uint16_t __bit_reverse(uint16_t x, uint16_t n) {
  uint16_t result = 0;
  for (uint16_t i = 0; i < n; i++) {
    if (x & (1 << i)) {
      result |= 1 << (n - 1 - i);
    }
  }
  return result;
}

// Function to compute the FFT
void fft(
	const uint16_t* const samples,
	const uint16_t samples_len)
{
	float* const real = __fft_out_real;
	float* const imag = __fft_out_imag;

	// Convert 16-bit unsigned integer samples to floating-point and
	// scale to the range -1.0 to 1.0
	for (uint16_t i = 0; i < samples_len; i++) {
		real[i] = (float) samples[i] / 32767.5f - 1.0f;
		imag[i] = 0.0f;
	}

	// Bit reversal permutation
	for (uint16_t i = 0; i < samples_len; i++) {
		uint16_t j = __bit_reverse(i, log2(samples_len));
		if (j > i) {
			// Swap real and imaginary components
			float temp = real[i];
			real[i] = real[j];
			real[j] = temp;
			temp = imag[i];
			imag[i] = imag[j];
			imag[j] = temp;
		}
	}

	// Butterfly stages
	for (uint16_t s = 1; s <= log2(samples_len); s++) {
		uint16_t m = 1 << s;
		float theta = 2.0 * 3.14 / m;
		for (uint16_t k = 0; k < samples_len; k += m) {
			float w_real = 1.0;
			float w_imag = 0.0;
			for (uint16_t j = 0; j < m / 2; j++) {
				uint16_t t = k + j;
				uint16_t u = t + m / 2;
				float t_real = w_real * real[u] - w_imag * imag[u];
				float t_imag = w_real * imag[u] + w_imag * real[u];

				real[u] = real[t] - t_real;
				imag[u] = imag[t] - t_imag;
				real[t] = real[t] + t_real;
				imag[t] = imag[t] + t_imag;

				float temp = w_real;
				w_real = temp * (float) cos(theta) - w_imag * (float) sin(theta);
				w_imag = temp * (float) sin(theta) + w_imag * (float) cos(theta);
			}
		}
	}
}

void psd(void)
{
	for (uint32_t i = 0; i < FFT_OUT_LEN; i++)
	{
		__fft_out_real[i] = powf(__fft_out_real[i], 2) + powf(__fft_out_real[i], 2);
	}

	return;
}
