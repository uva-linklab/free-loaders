# Imports
from utils.utils import *
import numpy as np

collect_save_data(block_size=100)

# Read
X = np.load('./data/dataX.npy')
Y = np.load('./data/dataY.npy')

print("Number of instances: ", X.shape[0])
print("Length of sequence: ", X.shape[1])
print("Number of channels: ", X.shape[2])


headers = ['chest_acc_x',
           'chest_acc_y', 'chest_acc_z', 'ecg_1', 'ecg_2',
           'left_ankle_acc_x', 'left_ankle_acc_y', 'left_ankle_acc_z',
           'left_ankle_gyro_x', 'left_ankle_gyro_y', 'left_ankle_gyro_z',
           'left_ankle_mag_x', 'left_ankle_mag_y', 'left_ankle_mag_z',
           'right_arm_acc_x', 'right_arm_acc_y', 'right_arm_acc_z',
           'right_arm_gyro_x', 'right_arm_gyro_y', 'right_arm_gyro_z',
           'right_arm_mag_x', 'right_arm_mag_y', 'right_arm_mag_z', 'label_Id']
