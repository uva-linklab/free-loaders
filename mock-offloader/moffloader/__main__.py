import argparse
import json
import random
import time
import numpy as np

import requests

ControllerHTTPPort = 8001


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def main(args):
    if args.task_id == None:
        offload_many(args.address,
                     args.device_id,
                     args.task_count,
                     args.rate)
    else:
        offload_one(args.address,
                    args.device_id,
                    args.task_id)


def offload_many(address, device_id, count, rate):
    intertask_delay = 1 / (rate / 60)
    print('Sending tasks every {} sec.'.format(intertask_delay))

    for i in range(0, count):
        # Send the task.
        task_id = random.randint(0, 29)  # Random selection.
        offload_one(address, device_id, task_id)
        time.sleep(intertask_delay)


def offload_one(address, device_id, task_id):
    payload = {
        'device_id': device_id,
        'task_id': task_id,
        'input_data': '',
    }

    if task_id < 10:
        # For loop task.
        payload['input_data'] = 0
        payload['deadline'] = 202 * (task_id + 1) + 854

    elif task_id < 20:
        # Matrix multiplication task.
        # Generate a matrix and send it as the input data.
        size = 750 + (83 * (task_id - 10))  # 750x750 -> ~1500x1500
        a = np.random.randint(low=1, high=256, size=(size,size), dtype=int)
        b = np.random.randint(low=1, high=256, size=(size,size), dtype=int)
        payload['input_data'] = {
            'a': a,
            'b': b,
        }
        payload['deadline'] = 41 * (task_id - 9) + 259 + 5000

    elif task_id < 30:
        # FFT task. 1s -> 10s of audio data
        samples = np.random.rand(44100 * (task_id - 19))

        payload['input_data'] = samples
        payload['deadline'] = 200 * (task_id - 19) + 2000

    # Send the task to the controller.
    url = 'http://{}:{}/submit-task'.format(address, ControllerHTTPPort)
    body_json = json.dumps(payload, cls=NumpyEncoder)
    # print('Sending task data {}'.format(body_json))
    try:
        response = requests.post(url, data=body_json, headers={'Content-Type': 'application/json'})
        print('Server says {}:', end='')
        for line in response.iter_lines():
            print('{}'.format(line))
    except requests.exceptions.ConnectionError:
        print('...cannot connect to server.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Task offloading utility')
    ap.add_argument('-d', '--device-id', help='Set the device ID.',
                    metavar='ID', type=int, default=0, dest='device_id')
    ap.add_argument('-t', '--task-id', help='Send a specific task.',
                    metavar='ID', type=int, dest='task_id')
    ap.add_argument('-n', '--task-count', help='Total number of tasks to send.',
                    metavar='COUNT', type=int, default=1000, dest='task_count')
    ap.add_argument('-r', '--rate', help='Rate to send tasks at (per min.).',
                    metavar='RATE', type=int, default=1000, dest='rate')

    ap.add_argument('address', help='Controller address')

    args = ap.parse_args()
    main(args)
