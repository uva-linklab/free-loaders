import argparse
import pickle

import librosa
import numpy as np
import sklearn.svm

_SampleRate = 11025
_SampleBufferLength = 4096

def classify_audio(samples):
    print('classifying {} received samples'.format(len(samples)))

    # Transform to floating point representation.
    samples = np.array(samples) / 32767.0

    print('  - loading model...')
    aec = None
    with open('executor/flexecutor/tasker/aec-svm.pkl', 'rb') as fh:
        aec = pickle.load(fh)

    print('  - calculating features...')
    rmse = librosa.feature.rms(y=samples)
    rmse_mean = np.mean(rmse)
    rmse_stdev = np.std(rmse)
    # print('  - RMSE mean = {:.4f}'.format(rmse_mean))
    # print('  - RMSE stdev = {:.4f}'.format(rmse_stdev))
    # print(np.max(samples))
    # return

    spectral_centroid = librosa.feature.spectral_centroid(
        y=samples,
        sr=_SampleRate,
        n_fft=_SampleBufferLength,
        hop_length=_SampleBufferLength)
    spectral_centroid_mean = np.mean(spectral_centroid)
    spectral_centroid_stdev = np.std(spectral_centroid)

    spectral_bandwidth = librosa.feature.spectral_bandwidth(
        y=samples,
        sr=_SampleRate,
        n_fft=_SampleBufferLength,
        hop_length=_SampleBufferLength)
    spectral_bandwidth_mean = np.mean(spectral_bandwidth)
    spectral_bandwidth_stdev = np.std(spectral_bandwidth)

    # print('  - centroid mean = {:.4f}'.format(spectral_centroid_mean))
    # print('  - bandwidth mean = {:.4f}'.format(spectral_bandwidth_mean))
    # print('  - centroid stdev = {:.4f}'.format(spectral_centroid_stdev))
    # print('  - bandwidth stdev = {:.4f}'.format(spectral_bandwidth_stdev))

    # MFCCs
    mfccs = librosa.feature.mfcc(
        y=samples,
        sr=_SampleRate,
        n_mfcc=13,
        n_fft=_SampleBufferLength,
        hop_length=_SampleBufferLength)
    mfccs_mean = np.mean(mfccs, axis=1)
    mfccs_stdev = np.std(mfccs, axis=1)

    # print('  - MFCCs mean: {}'.format(mfccs_mean))
    # print('  - MFCCs stdev: {}'.format(mfccs_stdev))

    features = np.concatenate(
        (np.array([rmse_mean,
                   rmse_stdev,
                   spectral_centroid_mean,
                   spectral_centroid_stdev,
                   spectral_bandwidth_mean,
                   spectral_bandwidth_stdev]),
         mfccs_mean,
         mfccs_stdev),)

    print('  - predicting...')
    p = aec.predict([features])
    print('  - prediction: {}'.format(p))

    return p

def _to_float_samples(sample):
    return float(sample) / 32767.0

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Audio event classification task.')
    ap.add_argument('path', help='Path to WAV file.',
                    type=str)

    args = ap.parse_args()

    import wave
    import time
    now = time.time()
    with wave.open(args.path, 'rb') as wfh:
        num_frames = wfh.getnframes()
        num_channels = wfh.getnchannels()
        sample_depth = wfh.getsampwidth()

        # Check if the sample width is 2 bytes (16 bits)
        if sample_depth != 2:
            raise ValueError("Only 16-bit WAV files are supported.")
        if num_channels != 1:
            raise ValueError("Only single-channel WAV files are supported.")

        # Read all frames from the WAV file
        frames = wfh.readframes(_SampleBufferLength)
        print('read {} bytes from file'.format(len(frames)))
        # Convert the raw bytes to a list of integers.  Use signed 16-bit integers.
        samples = np.frombuffer(frames, dtype='<i2')
        print('yields {} samples'.format(len(samples)))

        c = classify_audio(samples)
        print('event class: {}'.format(c))
        print(f'took a total of {time.time() - now} s')
