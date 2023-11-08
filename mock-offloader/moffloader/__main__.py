import argparse
import json
import random
import time
import numpy as np
import re
import os
import requests
import struct
import flomqtt.serialize as flserialize
from threading import Thread
import paho.mqtt.client as mqtt
import queue
from PIL import Image

ControllerHTTPPort = 8001
DeadlineMod = 1.0
SkipTasks = 0

msg_queue = queue.Queue()

def message_queue_processor():
    while True:
        message_json = msg_queue.get()

        task_id = message_json['task_id']
        job_id =  message_json['job_id']

        # offload the next task for the job
        next_task_index = current_submitted_task[job_id] + 3 # jump from "-base" to next "-base"
        next_task = schedule_plan[job_id][next_task_index]

        if next_task == 't':
            print(f'done with job_id={job_id}. current_submitted_task={current_submitted_task}')
        else:
            print(f'job_id={job_id}: task_id={task_id} finished. next task = {next_task}. current_submitted_task={current_submitted_task}')
            result = re.search(r"t(\d+)\-e(\d+)", next_task)
            task_id = int(result.group(1))
            executor_id = int(result.group(2))
            offload_one("localhost", 0, task_id, job_id=job_id, executor_id=executor_id)
            current_submitted_task[job_id] = next_task_index

        msg_queue.task_done()

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


controller_offloader_task_response_topic = "ctrl-offl-task-response"
current_submitted_task = {}
# schedule_plan = [['s0', 't9-e0-base', 't9-e0-thread', 't9-e0-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
#                  ['s1', 't9-e0-base', 't9-e0-thread', 't9-e0-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
#                  ['s2', 't9-e0-base', 't9-e0-thread', 't9-e0-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
#                  ['s3', 't9-e0-base', 't9-e0-thread', 't9-e0-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
#                  ['s4', 't9-e3-base', 't9-e3-thread', 't9-e3-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't']]
schedule_plan = [['s0', 't9-e0-base', 't9-e0-thread', 't9-e0-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
                 ['s1', 't9-e0-base', 't9-e0-thread', 't9-e0-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
                 ['s2', 't9-e0-base', 't9-e0-thread', 't9-e0-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
                 ['s3', 't9-e0-base', 't9-e0-thread', 't9-e0-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
                 ['s4', 't9-e3-base', 't9-e3-thread', 't9-e3-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
                 ['s5', 't9-e3-base', 't9-e3-thread', 't9-e3-end', 't19-e8-base', 't19-e8-thread', 't19-e8-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
                 ['s6', 't9-e3-base', 't9-e3-thread', 't9-e3-end', 't19-e0-base', 't19-e0-thread', 't19-e0-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
                 ['s7', 't9-e3-base', 't9-e3-thread', 't9-e3-end', 't19-e0-base', 't19-e0-thread', 't19-e0-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
                 ['s8', 't9-e4-base', 't9-e4-thread', 't9-e4-end', 't19-e0-base', 't19-e0-thread', 't19-e0-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't'],
                 ['s9', 't9-e4-base', 't9-e4-thread', 't9-e4-end', 't19-e0-base', 't19-e0-thread', 't19-e0-end', 't29-e8-base', 't29-e8-thread', 't29-e8-end', 't']]

def on_connect(client, userdata, flags, rc):
    print("[td] connected to mqtt with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(controller_offloader_task_response_topic, qos=2)

def on_subscribe(client, userdata, mid, granted_qos):
    offload_heteroedge(userdata["address"])

def on_message(client, userdata, mqtt_message):
    message_json = json.loads(mqtt_message.payload)
    msg_queue.put(message_json)

def on_disconnect(client, userdata, rc=0):
    print("DisConnected result code " + str(rc))
    client.loop_stop()

def connect(mqtt_client):
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.on_subscribe = on_subscribe

    mqtt_client.connect("localhost", 1883, 60)
    mqtt_client.loop_forever()

def main(args):
    if args.heteroedge:
        Thread(target=message_queue_processor).start()

        mqtt_client = mqtt.Client(client_id="moffloader", clean_session=True)
        mqtt_client.user_data_set({
            "address": args.address
        })
        clientloop_thread = Thread(target=connect, args=(mqtt_client,))
        clientloop_thread.start()
    else:
        if args.task_id == None:
            offload_many(args.address,
                         args.device_id,
                         args.task_count,
                         args.rate,
                         args.extended)
        else:
            offload_one(args.address,
                        args.device_id,
                        args.task_id)


def offload_heteroedge(address):
    global current_submitted_task, schedule_plan

    # offload the first task of each of the jobs
    for job_id, job_tasks in enumerate(schedule_plan):
        result = re.search(r"t(\d+)\-e(\d+)", job_tasks[1])
        task_id = int(result.group(1))
        executor_id = int(result.group(2))
        offload_one(address, 0, task_id, job_id=job_id, executor_id=executor_id)
        current_submitted_task[job_id] = 1


def offload_many(address, device_id, count, rate, extended):
    intertask_delay = 1 / (rate / 60)
    print('Sending tasks every {} sec.'.format(intertask_delay))

    # Skip N tasks, if specified.
    if SkipTasks > 0:
        print('Skipping the first {} tasks.'.format(SkipTasks))
        for i in range(0, SkipTasks):
            _x = random.randint(0, 29)

    for i in range(0, count):
        # Send the task.
        if extended == True:
            task_id = random.randint(30, 59)  # Random selection.
        else:
            task_id = random.randint(0, 29)

        offload_one(address, device_id, task_id)
        time.sleep(intertask_delay)

def offload_one(address, device_id, task_id, job_id=0, executor_id=None):
    # print(f'address={address}, device_id={device_id}, task_id={task_id}, job_id={job_id}, exec_id={executor_id}')
    task_data = {
        'device_id': device_id,
        'task_id': task_id,
        'job_id': job_id,
        'schedule_on_executor': executor_id
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

    elif task_id == 30:  # Object detection (AR headset)
        # TODO change deadline
        task_data['deadline'] = 15000
        # randomly select image from directory
        input_img_index = random.randint(1, 1)
        filepath = os.path.join('mock-offloader', 'moffloader', 'obj_det_input_files', f'test{input_img_index}.jpg')
        image = Image.open(filepath)

        # convert image to numpy array
        input_data_np = np.asarray(image, dtype=adt)
        input_data_shape = input_data_np.shape
        input_data_bytes = struct.pack('I', input_data_shape[0]) + \
                           struct.pack('I', input_data_shape[1]) + \
                           struct.pack('I', input_data_shape[2]) + \
                           input_data_np.tobytes()

    elif task_id == 31:  # Room classification (robot)
        # TODO change deadline
        task_data['deadline'] = 10000
        # randomly select image from directory
        # input_img_index = random.randint(1, 1)
        filepath = os.path.join('mock-offloader', 'moffloader', 'room_classification_input_files', f'00000003.jpg')
        image = Image.open(filepath).convert('RGB')

        # convert image to numpy array
        input_data_np = np.asarray(image, dtype=adt)
        input_data_shape = input_data_np.shape
        input_data_bytes = struct.pack('I', input_data_shape[0]) + \
                           struct.pack('I', input_data_shape[1]) + \
                           struct.pack('I', input_data_shape[2]) + \
                           input_data_np.tobytes()

    elif task_id == 32:  # Human Activity Recognition (smart watch)
        task_data['deadline'] = 7500

        # randomly generate HAR sample
        samples = np.random.rand(1, 100, 23)
        input_data_bytes = np.array(samples, dtype=adt).tobytes()

    # elif task_id < 40:
    #     # For loop + matrix multiplication
    #     task_data['deadline'] = (task_id - 30) * ((4350 - 925) / 9) + 925
    #     task_data['deadline'] += (task_id - 30) * ((20000 - 8250) / 9) + 8250
    #
    #     iters = (task_id - 29) * 1000000
    #
    #     size = 750 + (83 * (task_id - 30))
    #     m1_bytes = np.random.randint(low=1, high=256, size=(size,size), dtype=adt).tobytes()
    #     m2_bytes = np.random.randint(low=1, high=256, size=(size,size), dtype=adt).tobytes()
    #
    #     input_data_bytes = struct.pack('II', iters, len(m1_bytes)) + m1_bytes + m2_bytes
    #
    # elif task_id < 50:
    #     # For loop + FFT
    #     task_data['deadline'] = (task_id - 40) * ((4350 - 925) / 9) + 925
    #     task_data['deadline'] += (task_id - 40) * ((6000 - 2600) / 9) + 2600
    #
    #     iters = (task_id - 29) * 1000000
    #     samples = np.random.rand(44100 * (task_id - 39) * 3)
    #     input_data_bytes = struct.pack('I', iters) + np.array(samples, dtype=adt).tobytes()
    #
    # elif task_id < 60:
    #     # Matrix multiplication + FFT
    #     task_data['deadline'] = (task_id - 50) * ((20000 - 8250) / 9) + 8250
    #     task_data['deadline'] += (task_id - 50) * ((6000 - 2600) / 9) + 2600
    #
    #     size = 750 + (83 * (task_id - 50))
    #     m1_bytes = np.random.randint(low=1, high=256, size=(size,size), dtype=adt).tobytes()
    #     m2_bytes = np.random.randint(low=1, high=256, size=(size,size), dtype=adt).tobytes()
    #
    #     samples = np.random.rand(44100 * (task_id - 49) * 3)
    #     sample_bytes = np.array(samples, dtype=adt).tobytes()
    #
    #     input_data_bytes = struct.pack('I', len(m1_bytes)) + m1_bytes + m2_bytes + sample_bytes

    else:
        print('bad task ID: {}'.format(task_id))
        return

    task_data['deadline'] *= DeadlineMod

    task_json = json.dumps(task_data)
    http_post_data = flserialize.pack(task_json, input_data_bytes)

    # Send the task to the controller.
    url = 'http://{}:{}/submit-task'.format(address, ControllerHTTPPort)

    try:
        response = requests.post(url, data=http_post_data, headers={'Content-Type': 'application/octet-stream'})
        print('Server says:', end='')
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
    ap.add_argument('-e', '--extended', help='Use task IDs > 29',
                    action='store_true', default=False)
    ap.add_argument('--heteroedge', help='Submit heteroedge tasks',
                    action='store_true', default=False)
    ap.add_argument('--modulate-deadlines', help='Adjust deadlines by a factor.',
                    metavar='FACTOR', type=float, default=1.0, dest='deadline_mod')
    ap.add_argument('--seed', help='Specify a random seed',
                    metavar='SEED', type=int, default=time.gmtime(), dest='seed')
    ap.add_argument('--skip', help='Skip the first N offload tasks',
                    metavar='N', type=int, default=0, dest='skip')

    ap.add_argument('address', help='Controller address')


    args = ap.parse_args()

    SkipTasks = args.skip
    DeadlineMod = args.deadline_mod

    random.seed(args.seed)

    main(args)
