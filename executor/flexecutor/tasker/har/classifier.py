from torch import nn
from torch.nn import functional as F
from pytorch_lightning.core.module import LightningModule
import torch
import torch.optim as optim
from sklearn.metrics import f1_score


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

class Trainer:
    def __init__(self, model, loss_fn, config):
        self.model = model
        self.loss_fn = loss_fn
        self.optimizer = optim.Adam(self.model.parameters(), lr=config['lr'])
        self.num_epochs = config['num_epochs']

    def train_step(self, inputs, targets):
        # Forward pass
        predictions = self.model(inputs)
        loss = self.loss_fn(predictions, targets)

        # Backward pass
        self.optimizer.zero_grad()
        loss.backward()

        # Update model parameters
        self.optimizer.step()

        return loss

    def train(self, batches, valid_bateches):
        num_epochs = self.num_epochs
        for _ in range(num_epochs):
            for inputs, targets in batches:
                loss = self.train_step(inputs, targets)
            print (loss)
            f1 = self.validate(valid_bateches)
            print("Validation F1:", f1)

    def validate(self, dataloader):
        # Set the model to evaluation mode
        self.model.eval()
        predictions = []
        labels = []
        # Loop over the data in the dataloader
        for data, label in dataloader:
        # Forward pass through the model
            outputs = self.model(data)
            # Compute the loss
            loss = self.loss_fn(outputs, label)
            _, predicted = torch.max(outputs.data, 1)
            predictions.append(predicted)
            labels.append(label)
        # Return the validation loss
        predictions = [item for sublist in predictions for item in sublist]
        labels = [item for sublist in labels for item in sublist]
        f1 = f1_score(labels, predictions, average="micro")

        return f1

    def test(self, dataloader):
        # Set the model to evaluation mode
        self.model.eval()
        predictions = []
        labels = []
        # Loop over the data in the dataloader
        for data, label in dataloader:
        # Forward pass through the model
            outputs = self.model(data)
            # Compute the loss
            loss = self.loss_fn(outputs, label)
            _, predicted = torch.max(outputs.data, 1)
            predictions.append(predicted)
            labels.append(label)

        predictions = [item for sublist in predictions for item in sublist]
        labels = [item for sublist in labels for item in sublist]
        f1 = f1_score(labels, predictions, average="micro")

        # Return the test loss
        return f1
