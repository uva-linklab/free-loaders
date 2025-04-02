#!/bin/env python

import argparse
import csv

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

    # Match labels to the computed features.
    training_labels = []
    training_features = []
    with open(args.input, 'r') as csv_fh:
        csvr = csv.reader(csv_fh)
        skip_first_row = True
        for row in csvr:
            if skip_first_row:
                skip_first_row = False
                continue

            file_name = row[1]
            features = row[2:-18]
            # print(features)

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
    svm = sklearn.svm.SVC(gamma=0.1)
    svm.fit(scaler.transform(training_features), training_labels)

    # Try a prediction.
    # test_features = [0.03490791842341423,0.0172351635992527,2388.5721182472616,9.927971078438304,1593.426823329794,0.1586858984163655,46.78857421875,24.624492645263672,-1.86753511428833,1.6860706806182861,8.638815879821777,8.193831443786621,-3.1101269721984863,8.174623489379883,-5.257374286651611,10.82955551147461,3.18623948097229,9.704151153564453,-10.545510292053223,52.6614990234375,1.1996994018554688,1.398658275604248,1.354843258857727,0.04547595977783203,0.6796162128448486,0.24237525463104248,1.5520834922790527,0.9913158416748047,3.759599208831787,0.41292500495910645,0.26824235916137695,0.16008472442626953]

    # print(svm.predict(scaler.transform([test_features])))

    import micromlgen
    c_code = micromlgen.port(svm)
    with open('/tmp/svm.h', 'w') as fh:
        fh.write(c_code)

if __name__ == '__main__':

    ap = argparse.ArgumentParser(description='Build SVM model from features')
    ap.add_argument('labels', help='path to CSV containing labels')
    ap.add_argument('input', help='path to input CSV containing data')

    args = ap.parse_args()

    main(args)
