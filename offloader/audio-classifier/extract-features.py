#!/bin/env python

import argparse
import csv
import os
import os.path

import librosa
import numpy as np
import tqdm

def main(args):

    all_features = []
    it = tqdm.tqdm(
        _list_audio_files(args.path),
        total=len(list(_list_audio_files(args.path))),
        unit=' files')
    for file_name in it:

        path = os.path.join(args.path, file_name)

        samples = None
        sample_rate = None
        try:
            samples, sample_rate = librosa.load(path, sr=args.sample_rate, mono=True)
        except ValueError:
            continue

        if len(samples) < args.sample_buffer_len:
            samples = np.pad(samples, (0, args.sample_buffer_len - len(samples)), 'constant')
        else:
            samples = samples[:args.sample_buffer_len]

        rmse = librosa.feature.rms(y=samples)
        rmse_mean = np.mean(rmse)
        rmse_stdev = np.std(rmse)
        # print('  - RMSE mean = {:.4f}'.format(rmse_mean))
        # print('  - RMSE stdev = {:.4f}'.format(rmse_stdev))
        # print(np.max(samples))
        # return

        spectral_centroid = librosa.feature.spectral_centroid(
            y=samples,
            sr=sample_rate,
            n_fft=args.sample_buffer_len,
            hop_length=args.sample_buffer_len)
        spectral_centroid_mean = np.mean(spectral_centroid)
        spectral_centroid_stdev = np.std(spectral_centroid)

        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=samples,
            sr=sample_rate,
            n_fft=args.sample_buffer_len,
            hop_length=args.sample_buffer_len)
        spectral_bandwidth_mean = np.mean(spectral_bandwidth)
        spectral_bandwidth_stdev = np.std(spectral_bandwidth)

        # print('  - centroid mean = {:.4f}'.format(spectral_centroid_mean))
        # print('  - bandwidth mean = {:.4f}'.format(spectral_bandwidth_mean))
        # print('  - centroid stdev = {:.4f}'.format(spectral_centroid_stdev))
        # print('  - bandwidth stdev = {:.4f}'.format(spectral_bandwidth_stdev))

        # MFCCs
        mfccs = librosa.feature.mfcc(
            y=samples,
            sr=sample_rate,
            n_mfcc=13,
            n_fft=args.sample_buffer_len,
            hop_length=512)
        mfccs_mean = np.mean(mfccs, axis=1)
        mfccs_stdev = np.std(mfccs, axis=1)

        # print('  - MFCCs mean: {}'.format(mfccs_mean))
        # print('  - MFCCs stdev: {}'.format(mfccs_stdev))
        # return

        features = np.concatenate(
            (np.array([rmse_mean,
                       rmse_stdev,
                       spectral_centroid_mean,
                       spectral_centroid_stdev,
                       spectral_bandwidth_mean,
                       spectral_bandwidth_stdev]),
             np.array(list(_intersperse(mfccs_mean, mfccs_stdev))),))
        all_features.append((args.path, file_name, features.tolist(),))

    with open(args.output, 'w', newline='') as fh:
        csvw = csv.writer(fh)
        rows = ['path', 'file_name', 'rmse_mean', 'rmse_stdev', 'spectral_centroid_mean', 'spectral_centroid_stdev', 'spectral_bandwidth_mean', 'spectral_bandwidth_stdev']
        for i in range(0, len(mfccs_mean)):
            rows.append(f'mfcc_mean_{i}')
            rows.append(f'mfcc_stdev_{i}')
        csvw.writerow(rows)
        for (file_path, file_name, features,) in all_features:
            csvw.writerow([path, file_name] + features)

def _list_audio_files(dir_path):
    for path in os.listdir(dir_path):
        if path.endswith('.wav') or path.endswith('.flac'):
            yield path

def _intersperse(it1, it2):
    for (i1, i2) in zip(it1, it2):
        yield i1
        yield i2

if __name__ == '__main__':

    ap = argparse.ArgumentParser(description='Extract features from audio samples.')

    ap.add_argument('path', help='Path to audio sample audio files')
    ap.add_argument('output', help='Path to output CSV')

    ap.add_argument('-r', '--sample-rate', help='Specify sample rate.',
                    dest='sample_rate', type=int, default=11025)
    ap.add_argument('-b', '--sample-buffer-length', help='Specify sample buffer length.',
                    dest='sample_buffer_len', type=int, default=4096)

    args = ap.parse_args()

    main(args)
