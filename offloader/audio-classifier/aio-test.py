import argparse
import csv
import os.path

import librosa
import numpy as np
import sklearn.linear_model
import sklearn.neighbors
import sklearn.preprocessing
import sklearn.svm
import tqdm

def main(args):
    # Fetch labels from the metadata CSV.
    labels = None
    excluded_classes = args.exclude_classes.split(',')
    with open(args.labels_path, 'r') as csv_fh:
        csvr = csv.reader(csv_fh)
        _header = next(csvr)

        labels = { r[0]:r[7] for r in csvr if r[7] }
        print(f'Loaded {len(labels)} labels from {args.labels_path}.')
        # print(labels)

    excluded_files = [ k for (k,v,) in labels.items() if v in excluded_classes ]

    # Extract features for both datasets.
    print(f'Loading training data features from dataset at {args.train_path} ...')
    (train_file_names, train_features,) = _extract_features_dataset(args.train_path, excluded_files)
    train_labels = np.array([ labels[f] for f in train_file_names ])
    # print(train_labels)
    print(f'Loading testing data features from dataset at {args.test_path} ...')
    (test_file_names, test_features,) = _extract_features_dataset(args.test_path, excluded_files)
    test_labels = np.array([ labels[f] for f in test_file_names ])
    # print(test_labels)

    # Build the model.
    scaler = sklearn.preprocessing.StandardScaler()
    scaler.fit(train_features)
    # print(scaler.transform(train_features))

    svm = sklearn.svm.SVC(gamma=0.1)
    svm.fit(scaler.transform(train_features), train_labels)

    # lr = sklearn.linear_model.LogisticRegression()
    # lr.fit(train_features, train_labels)

    # nn = sklearn.neighbors.KNeighborsClassifier(n_neighbors=5)
    # nn.fit(train_features, train_labels)

    # Test precision.
    preds = svm.predict(scaler.transform(test_features))
    correct_preds = 0
    for (test_file_name, pred_label,) in zip(test_file_names, preds):
        actual_label = labels[test_file_name]
        if pred_label == actual_label:
            mark = '✅'
            correct_preds += 1
        else:
            mark = '❌'

        # print(f'Prediction for {test_file_name}: {actual_label} == {pred_label} ... {mark}')

    print(f'SVM precision: {correct_preds / len(preds) * 100:.2f}')

    # preds = lr.predict(test_features)
    # correct_preds = 0
    # for (test_file_name, pred_label,) in zip(test_file_names, preds):
    #     actual_label = labels[test_file_name]
    #     if pred_label == actual_label:
    #         mark = '✅'
    #         correct_preds += 1
    #     else:
    #         mark = '❌'

    # print(f'LR precision: {correct_preds / len(preds) * 100:.2f}')

    # preds = nn.predict(test_features)
    # correct_preds = 0
    # for (test_file_name, pred_label,) in zip(test_file_names, preds):
    #     actual_label = labels[test_file_name]
    #     if pred_label == actual_label:
    #         mark = '✅'
    #         correct_preds += 1
    #     else:
    #         mark = '❌'

    # print(f'KNN precision: {correct_preds / len(preds) * 100:.2f}')

def _extract_features_dataset(dataset_path, excluded_file_names=[], sample_rate=11025, sample_len=None):
    all_file_names = []
    all_features = []
    it = tqdm.tqdm(
        _list_audio_files(dataset_path, excluded_file_names),
        total=len(list(_list_audio_files(dataset_path, excluded_file_names))),
        unit=' files')
    for audio_file_name in it:
        audio_file_path = os.path.join(dataset_path, audio_file_name)
        features = _extract_features(audio_file_path, sample_rate, sample_len=sample_len)
        all_file_names.append(audio_file_name)
        all_features.append(features)

    return (np.array(all_file_names), np.array(all_features),)

def _extract_features(audio_file_path, sample_rate, sample_len=None, fft_size=512):
    try:
        samples, sample_rate = librosa.load(audio_file_path, sr=sample_rate, mono=True)
    except ValueError:
        pass

    if sample_len != None:
        if len(samples) < args.sample_len:
            samples = np.pad(samples, (0, sample_len - len(samples)), 'constant')
        else:
            samples = samples[:args.sample_len]

    # rmse = librosa.feature.rms(y=samples)
    # rmse_mean = np.mean(rmse)
    # rmse_stdev = np.std(rmse)

    # spectral_centroid = librosa.feature.spectral_centroid(
    #     y=samples,
    #     sr=sample_rate,
    #     n_fft=fft_size,
    #     hop_length=128)
    # spectral_centroid_mean = np.mean(spectral_centroid)
    # spectral_centroid_stdev = np.std(spectral_centroid)

    # spectral_bandwidth = librosa.feature.spectral_bandwidth(
    #     y=samples,
    #     sr=sample_rate,
    #     n_fft=fft_size,
    #     hop_length=128)
    # spectral_bandwidth_mean = np.mean(spectral_bandwidth)
    # spectral_bandwidth_stdev = np.std(spectral_bandwidth)

    # MFCCs
    mfccs = librosa.feature.mfcc(
        y=samples,
        sr=sample_rate,
        n_mfcc=13,
        n_fft=fft_size,
        hop_length=2048)
    mfccs_mean = np.mean(mfccs, axis=1)
    mfccs_stdev = np.std(mfccs, axis=1)

    features = np.concatenate(
        (np.array([
            # rmse_mean,
            # rmse_stdev,
            # spectral_centroid_mean,
            # spectral_centroid_stdev,
            # spectral_bandwidth_mean,
            # spectral_bandwidth_stdev
        ]),
         np.array(list(_intersperse(mfccs_mean, mfccs_stdev))),))

    return features

def _list_audio_files(dir_path, excluded_file_names=[]):
    excluded_file_names = set(excluded_file_names)
    for path in os.listdir(dir_path):
        if path.endswith('.wav') or path.endswith('.flac'):
            if path not in excluded_file_names:
                yield path

def _intersperse(it1, it2):
    for (i1, i2) in zip(it1, it2):
        yield i1
        yield i2

if __name__ == '__main__':

    ap = argparse.ArgumentParser(description='Build and test models.')

    ap.add_argument('-t', '--train-dataset-path', help='Path to the training dataset files.',
                    dest='train_path', type=str, default='./train')
    ap.add_argument('-v', '--test-dataset-path', help='Path to the testing dataset files.',
                    dest='test_path', type=str, default='./test')
    ap.add_argument('-l', '--labels-path', help='Path to the dataset labels.',
                    dest='labels_path', type=str, default='./labels.csv')
    ap.add_argument('--exclude-classes', help='Comma-delimited list of audio classes to exclude',
                    dest='exclude_classes', type=str, default='')

    args = ap.parse_args()

    main(args)
