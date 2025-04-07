#!/bin/env python

import argparse
import os
import sys
import wave

def convert_wav_to_c(wav_filename, c_filename, header_filename, max_samples=None):
    """
    Reads a WAV file, scales the samples to the range of a 16-bit unsigned integer,
    and generates a C source file and header file containing the samples.

    Args:
        wav_filename (str): The path to the input WAV file.
        c_filename (str): The path to the output C source file.
        header_filename (str): The path to the output header file.
        max_samples (int, optional): The maximum number of samples to include. Defaults to None (all samples).
    """
    try:
        with wave.open(wav_filename, 'rb') as wav_file:
            # Get WAV file parameters
            num_channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            num_frames = wav_file.getnframes()

            # Check if the sample width is 2 bytes (16 bits)
            if sample_width != 2:
                raise ValueError("Only 16-bit WAV files are supported. The input file has a sample width of {} bytes.".format(sample_width))

            # Read all frames from the WAV file
            frames = wav_file.readframes(num_frames)
            # Convert the raw bytes to a list of integers.  Use signed 16-bit integers
            samples = []
            if num_channels == 1:
                for i in range(0, len(frames), 2):
                    sample = frames[i] + (frames[i+1] << 8)
                    # Convert to signed 16 bit integer
                    if sample > 32767:
                        sample -= 65536
                    samples.append(sample)
            elif num_channels == 2:
                for i in range(0, len(frames), 4):
                    sample1 = frames[i] + (frames[i+1] << 8)
                    sample2 = frames[i+2] + (frames[i+3] << 8)
                    # Convert to signed 16 bit integer
                    if sample1 > 32767:
                        sample1 -= 65536
                    if sample2 > 32767:
                        sample2 -= 65536
                    samples.append(int((sample1 + sample2) / 2))
            else:
                raise ValueError("Only mono and stereo WAV files are supported.  The input file has {} channels.".format(num_channels))

            # Scale the samples to the range of 0 to 65535 (16-bit unsigned integer)
            max_sample_val = max(samples)
            min_sample_val = min(samples)
            if max_sample_val == min_sample_val:
                scale = 1.0
                offset = 32768
            else:
                scale = 65535.0 / (max_sample_val - min_sample_val)
                offset = -min_sample_val * scale

            scaled_samples = [int(sample * scale + offset) for sample in samples]
            # Truncate samples if max_samples is provided
            if max_samples is not None:
                scaled_samples = scaled_samples[:max_samples]

            # Generate C source code
            array_name = 'MDL_SampleAudio'
            with open(c_filename, 'w') as c_file:
                c_file.write("const unsigned short {}[] = {{\n    ".format(array_name))
                for i, sample in enumerate(scaled_samples):
                    c_file.write(f"{sample}")
                    if i < len(scaled_samples) - 1:
                        c_file.write(", ")
                    if (i + 1) % 16 == 0 and i + 1 != len(scaled_samples):  # Add newlines for readability
                        c_file.write("\n    ")
                c_file.write("\n};\n")

            # Generate header file
            with open(header_filename, 'w') as header_file:
                header_file.write("#ifndef MDL_WAVTOC_{}_H\n".format(array_name.upper()))
                header_file.write("#define MDL_WAVTOC_{}_H\n\n".format(array_name.upper()))

                header_file.write("#define MDL_WAVTOC_SAMPLE_AUDIO_LEN ((uint32_t) {})\n\n".format(len(scaled_samples)))

                header_file.write("extern const uint16_t {}[];\n\n".format(array_name))

                header_file.write("#endif\n")

    except wave.Error as e:
        print("Error reading WAV file: {}".format(e))
        sys.exit(1)
    except IOError as e:
        print("Error writing to file: {}".format(e))
        sys.exit(1)
    except ValueError as e:
        print("Error: {}".format(e))
        sys.exit(1)
    except Exception as e:
        print("An unexpected error occurred: {}".format(e))
        sys.exit(1)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate C code containing audio samples from a WAV file.")

    ap.add_argument("wav_file", help="Path to the WAV file.")
    ap.add_argument("--source-out-path", help="Path to the output C source file. Defaults to data.c in the current directory.",
                        dest='c_file', default="data.c")
    ap.add_argument("--header-out-path", help="Path to the output header file. Defaults to data.h in the current directory.",
                        dest='header_file', default="data.h")
    ap.add_argument("-n", "--max-samples", help="Maximum number of samples to include in the output array.",
                        dest='max_samples', default=None, type=int)

    args = ap.parse_args()

    wav_filename = args.wav_file
    c_filename = args.c_file
    header_filename = args.header_file
    max_samples = args.max_samples

    convert_wav_to_c(wav_filename, c_filename, header_filename, max_samples)
