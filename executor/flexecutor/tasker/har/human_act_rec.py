import torch
from classifier import ClassifierMHEALTH
from torch import nn
from torch.nn import functional as F
from pytorch_lightning.core.module import LightningModule

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

class LSTMEncoder(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers):
        super(LSTMEncoder, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)

    def forward(self, x, hidden=None):
        out, hidden = self.lstm(x, hidden)
        return out, hidden


class JOINTRepresentation(nn.Module):
    def __init__(self, common_dim, numofdim):
        super(JOINTRepresentation, self).__init__()
        self.common_dim = common_dim
        self.numofdim = numofdim
        # self.projector = nn.Linear(numofdim * 64, common_dim)
        self.LSTMEncoder = [0] * numofdim
        for i in range(numofdim):
            self.LSTMEncoder[i] = LSTMEncoder(100, 64, 1)
        self.chest_Sensors_projector = nn.Linear(len(chest_Sensors) * 64, common_dim)
        self.ecg_Sensors_projector = nn.Linear(len(ecg_Sensors) * 64, common_dim)
        self.left_ankle_Sensors_projector = nn.Linear(len(left_ankle_Sensors) * 64, common_dim)
        self.right_arm_Sensors_projector = nn.Linear(len(right_arm_Sensors) * 64, common_dim)
        self.whole_projector = nn.Linear(4 * common_dim, common_dim)

    def forward(self, x):
        x = x.permute(2,0,1)
        channel_start = 0
        output_list = []
        output_chest_Sensors = []
        for i in range(channel_start, channel_start + len(chest_Sensors)):
            output, _ = self.LSTMEncoder[i](x[i])
            output_chest_Sensors.append(output.view(output.size(0), -1))
        chest_Sensors_latent = self.chest_Sensors_projector(torch.cat(output_chest_Sensors, dim=-1))
        output_list.append(chest_Sensors_latent)
        channel_start += len(chest_Sensors)
        output_ecg_Sensors = []
        for i in range(channel_start, channel_start + len(ecg_Sensors)):
            output, _ = self.LSTMEncoder[i](x[i])
            output_ecg_Sensors.append(output.view(output.size(0), -1))
        ecg_Sensors_latent = self.ecg_Sensors_projector(torch.cat(output_ecg_Sensors, dim=-1))
        output_list.append(ecg_Sensors_latent)
        channel_start += len(ecg_Sensors)
        output_left_ankle_Sensors = []
        for i in range(channel_start, channel_start + len(left_ankle_Sensors)):
            output, _ = self.LSTMEncoder[i](x[i])
            output_left_ankle_Sensors.append(output.view(output.size(0), -1))
        left_ankle_Sensors_latent = self.left_ankle_Sensors_projector(torch.cat(output_left_ankle_Sensors, dim=-1))
        output_list.append(left_ankle_Sensors_latent)
        channel_start += len(right_arm_Sensors)
        output_right_arm_Sensors = []
        for i in range(channel_start, channel_start + len(right_arm_Sensors)):
            output, _ = self.LSTMEncoder[i](x[i])
            output_right_arm_Sensors.append(output.view(output.size(0), -1))
        right_arm_Sensors_latent = self.right_arm_Sensors_projector(torch.cat(output_right_arm_Sensors, dim=-1))
        output_list.append(right_arm_Sensors_latent)
        common_latent = torch.cat(output_list, dim=-1)
        return self.whole_projector(common_latent)

class ClassifierMHEALTH(LightningModule):
    def __init__(self, latent_dim):
        super().__init__()

        self.layer_1 = nn.Linear(latent_dim, 16)
        self.layer_2 = nn.Linear(16, 13)

    def forward(self, x):
        x = self.layer_1(x)
        x = F.relu(x)
        x = self.layer_2(x)
        return x

class MHEALTHClassification(nn.Module):
    def __init__(self, common_dim, numofdim):
        super(MHEALTHClassification, self).__init__()
        self.JOINTRepresentationModel = JOINTRepresentation(common_dim, numofdim)
        self.down_classifer = ClassifierMHEALTH(common_dim)

    def forward(self, x):
        representations = self.JOINTRepresentationModel(x)
        out = self.down_classifer(representations)
        return out

def run_har_task(input_data):
    model = MHEALTHClassification(16, 23)
    model.eval()
    outputs = model(input_data)
    _, predicted = torch.max(outputs.data, 1)
    return predicted


if __name__ == '__main__':
    sample_input = torch.rand(1, 100, 23).float()
    model = MHEALTHClassification(16, 23)
    model.eval()
    outputs = model(sample_input)
    _, predicted = torch.max(outputs.data, 1)
    print(predicted)
