# Author: Burak Himmetoglu (burakhmmtgl@gmail.com)
# Date  : 10-25-2017
#
# -- Utilities for mHealth dataset -- #

import numpy as np
import pandas as pd
import os
import requests
import zipfile
from sklearn.model_selection import train_test_split
import random
import torch
import torch.optim as optim
import copy

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# MHEALTH Headers
chest_Sensors = ['chest_acc_x', 'chest_acc_y', 'chest_acc_z']
ecg_Sensors = ['ecg_1', 'ecg_2']
left_ankle_Sensors = ['left_ankle_acc_x', 'left_ankle_acc_y', 'left_ankle_acc_z',
                      'left_ankle_gyro_x', 'left_ankle_gyro_y', 'left_ankle_gyro_z',
                      'left_ankle_mag_x', 'left_ankle_mag_y', 'left_ankle_mag_z']
right_arm_Sensors = ['right_arm_acc_x', 'right_arm_acc_y', 'right_arm_acc_z',
                     'right_arm_gyro_x', 'right_arm_gyro_y', 'right_arm_gyro_z',
                     'right_arm_mag_x', 'right_arm_mag_y', 'right_arm_mag_z']
labels = ['label_Id']

# mod_1 - Chest, mod_2 - Ecg, mod_3 - Left, mod_4 - Right
start = 0
mod_1 = list(range(start, start + len(chest_Sensors)))
start += len(chest_Sensors)
mod_2 = list(range(start, start + len(ecg_Sensors)))
start += len(ecg_Sensors)
mod_3 = list(range(start, start + len(left_ankle_Sensors)))
start += len(left_ankle_Sensors)
mod_4 = list(range(start, start + len(right_arm_Sensors)))
mod_indexes = {0: mod_1, 1: mod_2, 2: mod_3, 3: mod_4}

## Download and extract data files
def download_and_extract():
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00319/MHEALTHDATASET.zip"
    print("Downloading..")
    r = requests.get(url)

    # Write into file
    open('MHEALTHDATASET.zip','wb').write(r.content)

    # Extract
    print('Extracting...')
    zip_h = zipfile.ZipFile('MHEALTHDATASET.zip','r')
    zip_h.extractall()
    zip_h.close()

    # Rename and remove zip
    os.rename('MHEALTHDATASET', 'data')
    os.remove('MHEALTHDATASET.zip')

## Read data per subject
def read_subject(subject):
    """ Read measurements from a given subject """
    file_name = 'mHealth_subject' + str(subject) + '.log'
    file_path = os.path.join('data',file_name)


    # Read file
    try:
        df = pd.read_csv(file_path, delim_whitespace = True, header = None)
    except IOError:
        print("Data file does not exist!")

    # Remove data with null class (=0)
    df = df[df[23] != 0]

    return df

## Rewrite a sequence for a given subject in tensor format
def split_by_blocks(df, block_size=100):
    """ Split data from each subject into blocks of shorter length """

    # Channels
    n_channels = df.shape[1]-1

    # Group by labels
    grps = df.groupby(23)

    # Create a list for concatenating
    X_ = []
    Y_ = []

    # Loop over groups (labels), reshape to tensor and concatenate
    for ig in range(1,len(grps)+1,1):
        df_ = grps.get_group(ig)

        # Data and targets
        y = pd.unique(df_[23].values)
        x = df_.drop(23, axis=1).values

        n_blocks = len(x) // block_size
        x = x[:n_blocks*block_size]
        y = y[:n_blocks*block_size]

        x_tensor = x.reshape(-1, block_size, n_channels)

        # Append
        X_.append(x_tensor)
        Y_.append(np.array([y]*len(x_tensor), dtype=int).squeeze())

    # Concatenate and return
    X = np.concatenate(X_, axis=0)
    Y = np.concatenate(Y_, axis=0)

    return X, Y

## Merge all the subjects and save into file
def collect_save_data(subject_count = 10, block_size=100):
    """ Collects all the data from all the subjects and writes in file """

    # Initiate lists
    X_ = []
    Y_ = []
    for s in range(1,subject_count+1):

        # Read the data
        df = read_subject(s)

        # Split into blocks
        x,y = split_by_blocks(df, block_size)

        np.save(os.path.join('data','dataX_{}.npy'.format(s)), x)
        np.save(os.path.join('data','dataY_{}.npy'.format(s)), y)


        # Add to list
        X_.append(x)
        Y_.append(y)

    # Concatenate and save
    X = np.concatenate(X_, axis=0)
    Y = np.concatenate(Y_, axis=0)

    # Save
    np.save(os.path.join('data','dataX.npy'), X)
    np.save(os.path.join('data','dataY.npy'), Y)


## One-hot encoding
def one_hot(labels, n_class = 12):
    """ One-hot encoding """
    expansion = np.eye(n_class)
    y = expansion[:,labels-1].T

    return y

## Standardize
def standardize(X):
    """ Standardize by mean and std for each measurement channel"""
    return (X - np.mean(X, axis=0)[None,:,:]) / np.std(X, axis=0)[None,:,:]

def unison_shuffled_copies(a, b):
    assert len(a) == len(b)
    p = np.random.permutation(len(a))
    return a[p], b[p]

def generate_missing_modality_sets_with_index(batch):
    modality_indexes = [0, 1, 2, 3]
    for index in range(len(modality_indexes)):
        convert_batch = copy.deepcopy(batch.permute(2, 0, 1))
        copy_indexes = copy.deepcopy(modality_indexes)
        if not torch.isnan(convert_batch[mod_indexes[index]]).any():
            del copy_indexes[index]
            for other_index in copy_indexes:
                convert_batch[mod_indexes[other_index]] = np.nan
            yield (index, convert_batch.permute(1,2,0))
        else:
            continue


## Get batches
def get_batches(X, y, batch_size = 100, set_random_missing_modality = False, supervised=False, is_shuffled=False):
    """ Yield batches ffrom data """
    n_batches = len(X) // batch_size
    X, y = X[:n_batches*batch_size], y[:n_batches*batch_size]
    # Loop over batches and yield
    for b in range(0, len(X), batch_size):
        if set_random_missing_modality:
            index = random.choice([0, 1, 2, 3, 4])
            if index == 4:
                break
            random_X = X[b:b+batch_size].permute(2,0,1)
            if supervised:
                random_X[mod_indexes[index]] = 0
            else:
                random_X[mod_indexes[index]] = np.nan
            X[b:b+batch_size] = random_X.permute(1,2,0)
        final_X = X[b:b+batch_size]
        final_y =  y[b:b+batch_size]
        if is_shuffled:
            final_X, final_y = unison_shuffled_copies(X[b:b+batch_size], y[b:b+batch_size])
        yield final_X.to(device), final_y.to(device)

class Trainer:
    def __init__(self, model, model_config, train_params):
        self.model = model
        self.optimizer = optim.Adam(self.model.parameters(), lr=model_config['lr'])
        self.num_epochs = model_config['num_epochs']
        self.train_params = train_params

    def train_step(self, inputs, targets):
        # Forward pass
        loss, tqdm_dict = self.model.training_step(inputs, targets, self.train_params)

        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()

        # Update model parameters
        self.optimizer.step()

        return loss

    def train(self, batches):
        num_epochs = self.num_epochs
        for _ in range(num_epochs):
            for inputs, targets in batches:
                loss = self.train_step(inputs, targets)
            print (loss)
            # f1 = self.validate(valid_bateches)

    def validate(self, dataloader):
        # Set the model to evaluation mode
        self.model.eval()
        # Loop over the data in the dataloader
        for data, label in dataloader:
            # Forward pass through the model
            tqdm_dict = self.model.validation_step(data, self.train_params)

        return tqdm_dict


def FedAvg(w):
    w_avg = copy.deepcopy(w[0])
    # print(w_avg.keys())
    for k in w_avg.keys():
        for i in range(1, len(w)):
            w_avg[k] += w[i][k]
        w_avg[k] = torch.div(w_avg[k], len(w))
    return w_avg


def dist_l2(w, w_ema):
    a = 0.0
    for i in list(w.keys()) :
        a += (w[i]-w_ema[i]).float().norm(2)
    return a

def dist_l1(w):
    a = 0.0
    for i in list(w.keys()) :
        a +=  w[i].float().norm(1)
    return a


class Trainerwithoptuna:
    def __init__(self, model, trial):
        self.model = model
        lr = trial.suggest_float("lr", 1e-3, 1e-1, log=True)
        num_epochs = trial.suggest_int("num_epochs", 50, 250, step=50)
        optimizer_name = trial.suggest_categorical("optimizer", ["Adam", "SGD"])
        self.optimizer = getattr(optim, optimizer_name)(model.parameters(), lr=lr)
        # self.optimizer = optim.Adam(self.model.parameters(), lr=lr)
        self.num_epochs = num_epochs
        self.trial = trial

    def train_step(self, inputs, targets):
        # Forward pass
        temperature = self.trial.suggest_float("temperature", 0.2, 0.8, step=0.2)
        train_params = {"temperature":temperature}
        loss, tqdm_dict = self.model.training_step(inputs, targets, train_params)

        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()

        # Update model parameters
        self.optimizer.step()

        return loss

    def train(self, batches):
        num_epochs = self.num_epochs
        for _ in range(num_epochs):
            for inputs, targets in batches:
                loss = self.train_step(inputs, targets)
            print (loss)
            # f1 = self.validate(valid_bateches)

    def validate(self, dataloader):
        # Set the model to evaluation mode
        self.model.eval()
        # Loop over the data in the dataloader
        temperature = self.trial.suggest_float("temperature", 0.4, 0.6, step=0.1)
        train_params = {"temperature":temperature}
        for data, label in dataloader:
            # Forward pass through the model
            tqdm_dict = self.model.validation_step(data, train_params)

        return tqdm_dict