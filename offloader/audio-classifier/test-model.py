#!/usr/bin/env python

import argparse
import csv
import os
import os.path
import pickle

import librosa
import numpy as np
import sklearn.preprocessing
import sklearn.svm
import tqdm

_SampleRate = 11025
_SampleBufferLength = 4096

def main(args):

    # Load the model and scaler.
    aec_svm = None
    aec_scaler = None
    with open(args.model, 'rb') as fh:
        aec_svm = pickle.load(fh)
    with open(args.scaler, 'rb') as fh:
        aec_scaler = pickle.load(fh)

    # Load the labels as a map (file name -> label).
    labels = {}
    with open(args.labels, 'r') as csv_fh:
        csvr = csv.reader(csv_fh)
        _header = next(csvr)

        for row in csvr:
            audio_file_name = row[0]
            label = row[7]
            labels[audio_file_name] = label

        print(f'Loaded {len(labels)} labels.')

    # Make a prediction for each audio file.
    accuracy = [0, 0]
    it = tqdm.tqdm(
        enumerate(_list_audio_files(args.dataset)),
        unit=' files',
        total=len(list(_list_audio_files(args.dataset))))
    for (sample_no, audio_file_name) in it:
        if args.limit != None and sample_no >= args.limit:
            break

        path = os.path.join(args.dataset, audio_file_name)

        samples = None
        sample_rate = None
        try:
            samples, sample_rate = librosa.load(path, sr=_SampleRate, mono=True)
        except ValueError:
            continue

        if len(samples) < _SampleBufferLength:
            samples = np.pad(samples, (0, _SampleBufferLength - len(samples)), 'constant')
        else:
            samples = samples[:_SampleBufferLength]

        rmse = librosa.feature.rms(y=samples)
        rmse_mean = np.mean(rmse)
        rmse_stdev = np.std(rmse)

        spectral_centroid = librosa.feature.spectral_centroid(
            y=samples,
            sr=sample_rate,
            n_fft=_SampleBufferLength,
            hop_length=_SampleBufferLength)
        spectral_centroid_mean = np.mean(spectral_centroid)
        spectral_centroid_stdev = np.std(spectral_centroid)

        spectral_bandwidth = librosa.feature.spectral_bandwidth(
            y=samples,
            sr=sample_rate,
            n_fft=_SampleBufferLength,
            hop_length=_SampleBufferLength)
        spectral_bandwidth_mean = np.mean(spectral_bandwidth)
        spectral_bandwidth_stdev = np.std(spectral_bandwidth)

        # MFCCs
        mfccs = librosa.feature.mfcc(
            y=samples,
            sr=sample_rate,
            n_mfcc=13,
            n_fft=_SampleBufferLength,
            hop_length=_SampleBufferLength)
        mfccs_mean = np.mean(mfccs, axis=1)
        mfccs_stdev = np.std(mfccs, axis=1)

        features = np.concatenate(
            (np.array([rmse_mean,
                       rmse_stdev,
                       spectral_centroid_mean,
                       spectral_centroid_stdev,
                       spectral_bandwidth_mean,
                       spectral_bandwidth_stdev]),
             mfccs_mean,
             mfccs_stdev),)

        if args.embedded == True:
            features = features[:11]
        features = features.reshape(1, -1)

        pred = aec_svm.predict(aec_scaler.transform(features))
        actual = labels[audio_file_name]

        mark = '✅' if pred == actual else '❌'

        accuracy[0] += (1 if pred == actual else 0)
        accuracy[1] += 1

        # print(f'{mark} {audio_file_name} -> {pred} (actual: {labels[audio_file_name]})')

    print(f'Accuracy: {accuracy[0] / accuracy[1] * 100:.2f}%')

def _list_audio_files(dir_path):
    for path in os.listdir(dir_path):
        if path.endswith('.wav') or path.endswith('.flac'):
            yield path


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Get prediction accuracy results for a model')
    ap.add_argument('model', help='Path to model.',
                    type=str)
    ap.add_argument('scaler', help='Path to the scaler.',
                    type=str)
    ap.add_argument('dataset', help='Path to directory containing audio dataset files.',
                    type=str)
    ap.add_argument('labels', help='Path to CSV containing labels.',
                    type=str)

    ap.add_argument('-e', '--embedded-model', help='Indicate the model is the embedded one.',
                    dest='embedded', action='store_true', default=False)
    ap.add_argument('-l', '--limit', help='Limit to N predictions.', metavar='N',
                    dest='limit', type=int, default=None)

    args = ap.parse_args()

    main(args)
