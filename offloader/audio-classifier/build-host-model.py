#!/bin/env python

import argparse
import csv
import os
import os.path
import pickle

import numpy as np
import sklearn.preprocessing
import sklearn.svm

def main(args):

    # Build label dictionary.
    labels = {}
    with open(args.labels, 'r') as csv_fh:
        csvr = csv.reader(csv_fh)
        skip_first_row = True
        for row in csvr:
            if skip_first_row:
                skip_first_row = False
                continue

            labels[row[0]] = row[7]

        # Remove those that are not specified by --classes, if given.
        if args.classes != None:
            included_classes = args.classes.split(',')
            labels = { k: v for (k, v) in labels.items() if v in included_classes}
            print('Filtered labels to {} items.'.format(len(labels)))

    # Match labels to the computed features.
    training_labels = []
    training_features = []
    with open(args.input, 'r') as csv_fh:
        csvr = csv.reader(csv_fh)
        _header = next(csvr)
        for row in csvr:
            file_name = row[1]
            features = row[2:]
            # print(features)

            if file_name not in labels.keys():
                continue

            training_labels.append(labels[file_name])
            training_features.append(features)

    feature_count = len(training_features[0])
    print('feature count: {}'.format(len(training_features[0])))
    feature_arr = np.array(training_features, dtype=np.float32)
    for i in range(0, feature_count):
        # print(feature_arr[:,i])
        mean = np.mean(feature_arr[:,i])
        stdev = np.std(feature_arr[:,i])
        print('Feature {}: {:.3}, {:.3}'.format(i, mean, stdev))

    # Scale the training data.
    scaler = sklearn.preprocessing.StandardScaler()
    scaler.fit(training_features)
    # print(scaler.transform(training_features))

    # Build the SVM.
    svm = sklearn.svm.SVC(C=1000.0, gamma=0.1)
    svm.fit(scaler.transform(training_features), training_labels)

    # Try a prediction.
    test_features = []

    with open(args.output_path, 'wb') as fh:
        pickle.dump(svm, fh)

    # Output the scaler.
    scaler_output_path = os.path.join(os.path.split(args.output_path)[0], 'aec.stdscaler.pkl')
    with open(scaler_output_path, 'wb') as fh:
        pickle.dump(scaler, fh)

if __name__ == '__main__':

    ap = argparse.ArgumentParser(description='Build host SVM model from features.')
    ap.add_argument('-o', '--output', help='Path to output model.',
                    dest='output_path', type=str, default='./aec.svc.pkl')
    ap.add_argument('--classes', help='Restrict model to classes in a comma-separated list.', metavar='CLASSES',
                    type=str, dest='classes', default=None)
    ap.add_argument('labels', help='Path to CSV containing labels.')
    ap.add_argument('input', help='Path to input CSV containing data.')

    args = ap.parse_args()

    main(args)
