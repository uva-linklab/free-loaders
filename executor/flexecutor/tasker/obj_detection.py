import torch
from PIL import Image
import io

def run_obj_detection_task(image_bytes):
    # convert image_bytes to pillow image
    image = Image.open(io.BytesIO(image_bytes))

    # Model
    model = torch.hub.load("ultralytics/yolov5", "yolov5s")  # or yolov5n - yolov5x6, custom

    # Inference
    results = model(image)
    return str(results)

