#include <math.h>
#include <stdio.h>

#include <libtock-sync/peripherals/adc.h>

#include "acls.h"

#include "fft.h"
#include "svm.h"

float __spectral_bandwidth_frame(
	const uint16_t* const samples,
	const float centroid_freq);

float __mean(
	const float* const arr,
	const uint16_t arr_len);

float __stddev(
	const float* const arr,
	const uint16_t len,
	const float mean);

float __apply_triangular_filter(
	const float frequency_bin,
	const float center_frequency,
	const float bandwidth);

void __apply_filterbank(
	const float* const power_spectrum,
	const uint32_t spectrum_size,
	const float sampling_rate,
	float* const filterbank_output,
	const uint8_t num_filters);

void __dct(
	const float* const input,
	float* const output,
	const uint16_t input_size,
	const uint16_t output_size);

float __acls_buffer_a[ACLS_SAMPLE_LEN];
float __acls_buffer_b[ACLS_SAMPLE_LEN];

void check_initialize(void)
{
	// Write to the audio sample buffer to make sure the entire buffer is writeable.
	for (uint32_t i = 0; i < ACLS_SAMPLE_LEN; i++)
	{
		__acls_buffer_a[i] = 0xACFE;
		__acls_buffer_b[i] = 0xACFE;
	}

	return;
}

void classify(
	uint16_t* const sample_buffer)
{
	float features[11];

	/* libtocksync_adc_sample_buffer( */
	/* 	0, */
	/* 	ACLS_SAMPLE_FREQ, */
	/* 	sample_buffer, */
	/* 	/\* ACLS_SAMPLE_LEN *\/ */
	/* 	128 */
	/* 	); */

	// +     146 ms
	rmse_statistics(sample_buffer, features);
	// +   3,629 ms
    fft(sample_buffer, 256, __acls_buffer_a, __acls_buffer_b);
	// +      29 ms
	centroid_statistics(__acls_buffer_a, features + 2);
	// +   1,465 ms
	/* const float* const coefs = */
	/* 	mfccs(__acls_buffer_a, __acls_buffer_b, __acls_buffer_b); */
	// +   8,485 ms
	/* spectral_bandwidth(sample_buffer, features[2], features + 4); */
	// ------------
	//     13,765 ms (observed)

	// +       89 ms
	/* predict(features); */
	// ------------
	//     8,915 ms

	return;
}

#define ACLS_RMSE_FRAME_SAMPLE_LEN ((uint32_t) 2048)
#define ACLS_RMSE_TOTAL_FRAMES ((uint32_t) ((ACLS_SAMPLE_LEN / ACLS_RMSE_FRAME_SAMPLE_LEN)) \
								+ (ACLS_SAMPLE_LEN % ACLS_RMSE_FRAME_SAMPLE_LEN == 0 ? 0 : 1))

void rmse_statistics(
	const uint16_t* const samples,
	float* const statistics_out)
{
	float frame_rmse[ACLS_RMSE_TOTAL_FRAMES];

	for (uint16_t frame_no = 0; frame_no < ACLS_RMSE_TOTAL_FRAMES; frame_no++)
	{
		const uint16_t frame_offset = frame_no * ACLS_RMSE_FRAME_SAMPLE_LEN;
		const uint16_t frame_boundary = frame_offset + ACLS_RMSE_FRAME_SAMPLE_LEN <= ACLS_SAMPLE_LEN ?
			frame_offset + ACLS_RMSE_FRAME_SAMPLE_LEN : ACLS_SAMPLE_LEN;
		for (uint16_t sample_no = frame_offset; sample_no < frame_boundary; sample_no++)
		{
			const float fsmp = (((float) samples[sample_no]) / 32767.0) - 1.0;
			frame_rmse[frame_no] += fsmp * fsmp;
		}

		frame_rmse[frame_no] = sqrtf(frame_rmse[frame_no] / ACLS_RMSE_FRAME_SAMPLE_LEN);
	}

	statistics_out[0] = __mean(frame_rmse, ACLS_RMSE_TOTAL_FRAMES);
	statistics_out[1] = __stddev(frame_rmse, ACLS_RMSE_TOTAL_FRAMES, statistics_out[0]);

	return;
}

void centroid_statistics(
	const float* const fdm,
	float* statistics_out)
{
	float total_energy = 0.0;
	for (uint16_t i = 0; i < 256 / 2; i++)
	{
		total_energy += fdm[i];
	}

	float acc_energy = 0.0;
	uint16_t centroid_idx = 0;
	for (; acc_energy < total_energy / 2; centroid_idx++)
	{
		acc_energy += fdm[centroid_idx];
	}
	statistics_out[0] = fdm[centroid_idx];

	statistics_out[1] = __stddev(fdm, ACLS_SAMPLE_LEN, total_energy / ACLS_SAMPLE_LEN);

	return;
}

#define ACLS_SB_FRAME_SAMPLE_LEN 2048
#define ACLS_SB_FRAME_HOP_SAMPLE_LEN 512
// Calculate how many frames can be created by "hopping" forward by the hop length.
#define ACLS_SB_FRAME_COUNT \
	1 + (ACLS_SAMPLE_LEN - ACLS_SB_FRAME_SAMPLE_LEN)	\
	/ ACLS_SB_FRAME_HOP_SAMPLE_LEN

void spectral_bandwidth(
	const uint16_t* const samples,
	const float centroid_freq,
	float* const statistics_out)
{
	float frames_sb[ACLS_SB_FRAME_COUNT];
	for (uint32_t frame_no = 0; frame_no < ACLS_SB_FRAME_COUNT; frame_no++)
	{
		frames_sb[frame_no] = __spectral_bandwidth_frame(
			samples + (ACLS_SB_FRAME_HOP_SAMPLE_LEN * frame_no),
			centroid_freq);
	}

	// Normalize each frame's total energy.
	float sum_exp = 0.0;
	// Get the exponentiated sum.
	for (uint32_t i = 0; i < ACLS_SB_FRAME_COUNT; i++)
	{
		sum_exp += expf(frames_sb[i]);
	}
	// Calculate the normalized values.
	for (uint32_t i = 0; i < ACLS_SB_FRAME_COUNT; i++)
	{
		frames_sb[i] = expf(frames_sb[i]) / sum_exp;
	}

	statistics_out[0] = __mean(frames_sb, ACLS_SB_FRAME_COUNT);
	statistics_out[1] = __stddev(frames_sb, ACLS_SB_FRAME_COUNT, statistics_out[0]);

	return;
}

/** Calculate the spectral bandwidth of a single frame.
 */
float __spectral_bandwidth_frame(
	const uint16_t* const samples,
	const float centroid_freq)
{
	// Formula:
	// (sum_k S[k, t] * (freq[k, t] - centroid[t])**p)**(1/p)
	//
	// For the case of a single frame of audio:
	// (sum_k: S[k] * (freq[k] - centroid)^p)^(1/p)
	fft(samples, 256, __acls_buffer_a, __acls_buffer_b);
	const float* const fdm = __acls_buffer_a;
	// e = sum_k S[k] * (freq[k] - centroid)^2
	float e = 0.0;
	for (uint32_t i = 0; i < 256 / 2; i++)
	{
		const uint32_t bin_freq = i * ACLS_SAMPLE_FREQ / 256;
		e += fdm[i] * pow(bin_freq - centroid_freq, 2);
	}

	const float bw = sqrtf(e);

	return bw;
}

#define ACLS_MFCC_FILTER_COUNT ((uint32_t) 20)
#define ACLS_MFCC_DCT_OUTPUT_LEN ((uint32_t) 13)

#define ACLS_MFCC_FRAME_SAMPLE_LEN 2048
#define ACLS_MFCC_FRAME_HOP_SAMPLE_LEN 512
// Calculate how many frames can be created by "hopping" forward by the hop length.
#define ACLS_MFCC_FRAME_COUNT \
	1 + (ACLS_SAMPLE_LEN - ACLS_SB_FRAME_SAMPLE_LEN)	\
	/ ACLS_SB_FRAME_HOP_SAMPLE_LEN

float __acls_mfcc_filterbank_output[ACLS_MFCC_FILTER_COUNT];
float __acls_mfcc_dct_output[ACLS_MFCC_DCT_OUTPUT_LEN];

float* mfccs(
	const float* const fdm_real,
	const float* const fdm_imag,
	float* const psd_scratch)
{
	// This implementation treats the entire input as a frame.
	psd(fdm_real, fdm_imag, psd_scratch, ACLS_SAMPLE_LEN);
	const float* const psd = psd_scratch;

	__apply_filterbank(
		psd,
		ACLS_SAMPLE_LEN,
		ACLS_SAMPLE_FREQ,
		__acls_mfcc_filterbank_output,
		20);

	__dct(__acls_mfcc_filterbank_output,
		  __acls_mfcc_dct_output,
		  ACLS_MFCC_FILTER_COUNT,
		  ACLS_MFCC_DCT_OUTPUT_LEN);

	return __acls_mfcc_dct_output;
}

float __mean(
	const float* const arr,
	const uint16_t arr_len)
{
	if (arr_len == 0)
	{
		return 0.0f;
	}

	float sum = 0.0;
	for (uint16_t i = 0; i < arr_len; i++)
	{
		sum += arr[i];
	}

	return sum / arr_len;
}

float __stddev(
	const float* const arr,
	const uint16_t arr_len,
	const float mean)
{
	if (arr_len <= 1)
	{
		return 0.0f;
	}

	float sum_sq_diff = 0.0f;
	for (int i = 0; i < arr_len; i++)
	{
		sum_sq_diff += powf(arr[i] - mean, 2);
	}

	return sqrtf(sum_sq_diff / (arr_len - 1));
}

float __apply_triangular_filter(
	const float frequency_bin,
	const float center_frequency,
	const float bandwidth)
{
    if (frequency_bin < center_frequency - bandwidth / 2.0f
		|| frequency_bin > center_frequency + bandwidth / 2.0f)
	{
        return 0.0f; // Outside the filter's range
    }
	else if (frequency_bin <= center_frequency)
	{
        return (frequency_bin - (center_frequency - bandwidth / 2.0f)) / (bandwidth / 2.0f); // Rising slope
    }
	else
	{
        return ((center_frequency + bandwidth / 2.0f) - frequency_bin) / (bandwidth / 2.0f); // Falling slope
    }
}

// Function to apply a filter bank to a power spectrum
void __apply_filterbank(
	const float* const power_spectrum,
	const uint32_t spectrum_size,
	const float sampling_rate,
	float* const filterbank_output,
	const uint8_t num_filters)
{
    float min_mel = 0.0f;
    float max_mel = 2595.0f * log10(1.0f + sampling_rate / (2.0f * 700.0f)); // Max mel frequency

    float mel_spacing = (max_mel - min_mel) / (num_filters + 1); // Calculate mel spacing between filters
    float mel_centers[num_filters];

    // Calculate center frequencies in Mel scale
    for (int i = 0; i < num_filters; i++)
	{
        mel_centers[i] = min_mel + (i + 1) * mel_spacing;
    }

    // Convert Mel center frequencies to linear frequencies
    float center_frequencies[num_filters];
    for (int i = 0; i < num_filters; i++)
	{
        center_frequencies[i] = 700.0f * (pow(10.0f, mel_centers[i] / 2595.0f) - 1.0f);
    }

    // Calculate filter bandwidths (assuming equal bandwidths for simplicity)
    float bandwidth = center_frequencies[1] - center_frequencies[0];

    // Apply the filter bank
    for (uint32_t i = 0; i < num_filters; i++)
	{
        filterbank_output[i] = 0.0f;
        for (uint32_t j = 0; j < spectrum_size; j++)
		{
            float frequency_bin = (float) j * sampling_rate / (float) (2 * spectrum_size); // Calculate frequency of bin
            filterbank_output[i] += power_spectrum[j] * __apply_triangular_filter(frequency_bin, center_frequencies[i], bandwidth);
        }
    }

	return;
}

void __dct(
	const float* const input,
	float* const output,
	const uint16_t input_size,
	const uint16_t output_size)
{
    for (int k = 0; k < output_size; k++)
	{
        output[k] = 0.0f;
        for (int n = 0; n < input_size; n++)
		{
            output[k] += input[n] * cos(M_PI * (n + 0.5f) * k / input_size);
        }
        output[k] *= sqrt(2.0f / input_size);
        if (k == 0)
		{
            output[k] *= 1.0f / sqrt(2.0f);
        }
    }

	return;
}
