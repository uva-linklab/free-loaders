# Generates a standard scaler for the input state of few runs of the task scheduler
import argparse
import os.path

from sklearn.preprocessing import StandardScaler
from joblib import dump
import pandas as pd

ap = argparse.ArgumentParser()

ap.add_argument('path', help='path to observation CSV file', type=str)
args = ap.parse_args()

(basename, _ext) = os.path.splitext(args.path)

# fetch data from a file
data = pd.read_csv(args.path, header=None).values
scaler = StandardScaler()
scaler.fit(data)
scalerd_data = scaler.transform(data)

dump(scaler, '{}{}'.format(basename, '.bin'), compress=True)
