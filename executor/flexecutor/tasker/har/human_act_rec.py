import sys
import torch

def run_har_task(input):
    model = torch.load('model/har-model.pt')
    model.eval()

    outputs = model(input)
    _, predicted = torch.max(outputs.data, 1)
    return predicted

if __name__ == '__main__':
    batch_size = int(sys.argv[1])
    input = torch.rand(batch_size, 100, 23)
    print(run_har_task(input))
