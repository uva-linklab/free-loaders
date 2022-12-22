import argparse
import json
import random
import time
import numpy as np

import requests
import struct
import flomqtt.serialize as flserialize

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
    task_data = {
        'device_id': device_id,
        'task_id': task_id
    }

    http_post_data = b''
    # Define a consistent byte order.
    adt = np.dtype('<i4')

    if task_id < 10:
        # For loop task.
        task_data['deadline'] = task_id * ((4350-925)/9) + 925

        input_data = (task_id + 1) * 1000000  # 1,000,000 -> 10,000,000 loops
        input_data_bytes = struct.pack('I', input_data)

    elif task_id < 20:
        # Matrix multiplication task.
        task_data['deadline'] = (task_id - 10) * ((20000-8250)/9)+8250

        # Generate a matrix and send it as the input data.
        size = 750 + (83 * (task_id - 10))  # 750x750 -> ~1500x1500
        m1_bytes = np.random.randint(low=1, high=256, size=(size,size), dtype=adt).tobytes()
        m2_bytes = np.random.randint(low=1, high=256, size=(size,size), dtype=adt).tobytes()
        # Serialize the numpy arrays, placing the length of the first matrix as the first piece of data.
        input_data_bytes = struct.pack('I', len(m1_bytes)) + m1_bytes + m2_bytes

    elif task_id < 30:
        # FFT task. 3s -> 30s of audio data
        task_data['deadline'] = (task_id - 20) * ((6000-2600)/9)+2600
        samples = np.random.rand(44100 * (task_id - 19) * 3)
        input_data_bytes = np.array(samples, dtype=adt).tobytes()

    else:
        print('bad task ID: {}'.format(task_id))
        return

    task_json = json.dumps(task_data)
    http_post_data = flserialize.pack(task_json, input_data_bytes)

    # Send the task to the controller.
    url = 'http://{}:{}/submit-task'.format(address, ControllerHTTPPort)

    try:
        response = requests.post(url, data=http_post_data, headers={'Content-Type': 'application/octet-stream'})
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
