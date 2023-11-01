import torch

def run_obj_detection_task(image_bytes):
    # Model
    model = torch.hub.load("ultralytics/yolov5", "yolov5s")  # or yolov5n - yolov5x6, custom

    # Inference
    results = model(image_bytes)
    return str(results)

