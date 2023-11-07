import torch
from torchvision import transforms
from PIL import Image
import numpy as np

def run_room_classification_task(image_bytes):
    img_size = 512

    # Load the model for testing
    model = torch.load('executor/flexecutor/tasker/room_classification/models/squeezenet_0.pth', map_location=torch.device('cpu'))
    model.eval()

    # Preprocessing transformations
    preprocess = transforms.Compose([
        transforms.Resize(size=img_size),
        transforms.CenterCrop(size=img_size),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225])])

    # use cpu for inference as it is faster than the gpu on the cuda devices we have
    device="cpu"

    # Perform prediction and plot results
    with torch.no_grad():
        # get Pillow image from a numpy array
        # https://stackoverflow.com/questions/55319949/pil-typeerror-cannot-handle-this-data-type
        img = Image.fromarray((image_bytes * 255).astype(np.uint8))
        inputs = preprocess(img).unsqueeze(0).to(device)
        outputs = model(inputs)
        res = str(torch.max(outputs.data, 1)[1])
        return res



