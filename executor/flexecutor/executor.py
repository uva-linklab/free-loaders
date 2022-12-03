import json
import log
import signal
import struct
import sys
import threading
import time
from multiprocessing import Process, Pipe

import flomqtt.serialize as flserialize
import paho.mqtt.client

import config
import stats
from tasker.loop import run_loop_task
from tasker.fft import run_fft_task

# MQTT server port; fixed to 1883.
MQTTServerPort = 1883

# Topic the controller uses to send tasks for execution to executors.
MQTTTopicExecuteTask = 'ctrl-exec-task-execute'
# Topic the executor uses to send responses back to the controller.
MQTTTopicTaskResponse = 'exec-ctrl-task-response'

def start_executor(controller_addr, executor_id, power, log_level):
    '''Launches the task executor process.

    Accepts the ID to use as its executor ID, which it uses to listen for work.
    '''

    p = Process(name='executor',
                target=__executor_entry,
                args=(controller_addr, executor_id, power, log_level))
    p.start()

    return p

def __executor_entry(controller_addr, executor_id, power, log_level):
    '''Executor thread entry function.

    Listens for MQTT messages carrying tasks to run.
    Spins of new threads to perform work.
    '''

    config.configure_process('executor')
    signal.signal(signal.SIGALRM, __signal_handler)

    log.i('started')

    mqtt_client = paho.mqtt.client.Client(client_id=f"flexecutor-{executor_id}",
                                          clean_session=False,
                                          userdata={'executor_id': executor_id, 'power': power})
    mqtt_client.on_connect = __mqtt_on_connect
    mqtt_client.on_message = __mqtt_message_received
    mqtt_client.on_disconnect = __mqtt_on_disconnect

    log.i('connecting to {}:{}'.format(controller_addr, MQTTServerPort))

    # Attempt to connect to the MQTT server.
    # This code has grown an issue since breaking it into a subprocess
    # where the client does not want to connect, just forever hanging
    # somewhere in the client code.
    #
    # We use SIGALRM to get out of this hang and kill the process when this happens.
    # The top fLexecutor process will start the subprocess again and it can then try again,
    # when it is more likely to succeed, for some reason.
    while True:
        try:
            signal.alarm(2)
            mqtt_client.connect(controller_addr, MQTTServerPort)
            break
        except ConnectionRefusedError:
            signal.alarm(0)
            log.e('connection refused')
            time.sleep(2)

    signal.alarm(0)

    log.d('entering MQTT client loop')
    mqtt_client.loop_forever()

def __signal_handler(signal_no, stack_frame):
    '''Signal handler for the executor subprocess.

    This is just used to handle the case if the MQTT connect hangs.
    '''

    if signal_no == signal.SIGALRM:
        log.w('MQTT client did not connect in time; exiting...')
        sys.exit(1)
    else:
        log.e('Unhandled signal {} define the executor signal handler.'.format(signal_no))
        sys.exit(1)

def __mqtt_on_connect(client, userdata, flags, rc):
    log.i('Connected to server with result: {}'.format(rc))
    topic = f'{MQTTTopicExecuteTask}-{userdata["executor_id"]}'
    client.subscribe(topic, qos=2)
    log.i(f'subscribed to {topic}')

def __mqtt_on_disconnect(client, userdata, rc=0):
    log.w('Disconnected from server: {}'.format(rc))

def __mqtt_message_received(client, data, msg):
    # log.i('received message (on {})'.format(msg.topic))

    topic = f'{MQTTTopicExecuteTask}-{data["executor_id"]}'

    if msg.topic == topic:
        (task_json, additional_data) = flserialize.unpack(msg.payload)
        task_request = json.loads(task_json)
        # Check fields.
        for k in ['task_id', 'executer_id', 'offload_id']:
            if k not in task_request:
                log.w('Task request is malformed.')

        log.i(f'offload_id={task_request["offload_id"]}. request to execute task_id={task_request["task_id"]} ')
        __execute_task(client, data["executor_id"], data['power'], task_request, additional_data)

def __execute_task(client, executor_id, power, task_request, additional_data):
    '''Begin executing a task in a new thread.

    Sends a response to the controller after completion.
    '''
    # log.i(f'offload_id={task_request["offload_id"]}. in __execute_task')
    thread = threading.Thread(target=__executor_task_entry,
                              # Hm. Is the MQTT client thread-safe?
                              args=(client, executor_id, power, task_request, additional_data))
    thread.start()
    # log.i(f'offload_id={task_request["offload_id"]}. thread created.')

    return thread

# Task execution timeout.
ExecutionTimeout = 2 * 60

def __executor_task_entry(mqtt_client, executor_id, power, task_request, additional_data):
    # log.i(f'offload_id={task_request["offload_id"]}. in __executor_task_entry')
    (p_recv, p_send) = Pipe([False])
    process = Process(target=__process_task_entry, args=(p_send, executor_id, power, task_request, additional_data))
    # log.i(f'offload_id={task_request["offload_id"]}. created process object')
    try:
        # log.i(f'offload_id={task_request["offload_id"]}. before process.start()')
        process.start()
        # log.i(f'offload_id={task_request["offload_id"]}. finished process.start(). PID={process.pid}. process.is_alive()={process.is_alive()}')

        p_send.close()

        # log.i(f'offload_id={task_request["offload_id"]}. finished p_send.close()')

        result = p_recv.recv()  # block and waits for data from the process

        # log.i(f'offload_id={task_request["offload_id"]}. finished result = p_recv.recv()')

        process.join(ExecutionTimeout)  # wait for process to finish up
        log.i(f'offload_id={task_request["offload_id"]}. after process.join()')
        # check if the process exited
        if process.exitcode is not None:
            log.i(f'offload_id={task_request["offload_id"]}. process finished gracefully.')
            mqtt_client.publish(MQTTTopicTaskResponse,
                                result,
                                qos=2)
        else:
            process.terminate()
            log.i(f'offload_id={task_request["offload_id"]}. process failed to join. timed out. terminated.')
            current_state = stats.fetch()
            response = {
                'executor_id': task_request['executer_id'],
                'task_id': task_request['task_id'],
                'offload_id': task_request['offload_id'],
                'state': current_state,
                'energy': power * ExecutionTimeout,
                'status': process.exitcode  # inform the controller that we failed
            }
            mqtt_client.publish(MQTTTopicTaskResponse,
                                flserialize.pack(json.dumps(response), b''),
                                qos=2)
            log.i(f'offload_id={task_request["offload_id"]}. finished mqtt_client.publish')

    except (EOFError, OSError):
        log.e(f'offload_id={task_request["offload_id"]}. process failed with exit code = {process.exitcode}')
        # Collect current state and send it, along with the result.
        current_state = stats.fetch()
        response = {
            'executor_id': task_request['executer_id'],
            'task_id': task_request['task_id'],
            'offload_id': task_request['offload_id'],
            'state': current_state,
            'energy': 0,
            'status': process.exitcode  # inform the controller that we failed
        }
        mqtt_client.publish(MQTTTopicTaskResponse,
                            flserialize.pack(json.dumps(response), b''),
                            qos=2)
        log.i(f'offload_id={task_request["offload_id"]}. finished mqtt_client.publish')
    except Exception as error:
        log.i(f'offload_id={task_request["offload_id"]}. hit exception!')
        log.e(error)
    finally:
        # log.i(f'offload_id={task_request["offload_id"]}. in finally block')
        p_recv.close()
        # log.i(f'offload_id={task_request["offload_id"]}. finished finally block')

def __process_task_entry(pipe, executor_id, power, task_request, additional_data):
    '''Task execution process entry.

    Executes the task and sends the result and state to the controller.
    '''

    # log.e(f'offload_id={task_request["offload_id"]}. in __process_task_entry')
    config.configure_process()

    # Lower process priority.
    # os.nice(12)

    # log.i('executing task')
    start_time = time.time()
    # log.i(f'offload_id={task_request["offload_id"]}. executing task')
    # Execute task here.
    # TODO: update tasks that need to use data from files.
    task_id = task_request['task_id']

    res_data = b''
    # TODO: remove hardcoding
    cuda_executors = [0, 8, 9]

    if task_id < 10:
        # Additional data is the value to start loop iterations with.
        loop_iter_count = struct.unpack('I', additional_data[:4])[0]
        res = run_loop_task(loop_iter_count)
        res_data = struct.pack('I', res)
    elif task_id < 20:
        # Additional data is the length of the first matrix, the first matrix, and the second matrix.
        first_matrix_data_len = struct.unpack('I', additional_data[:4])[0]
        matrix_a_bytes = additional_data[4:(4+first_matrix_data_len)]
        matrix_b_bytes = additional_data[(4+first_matrix_data_len):]

        # Recover the matrices, including their lost shape.
        if executor_id in cuda_executors:
            import cupy as np
            from tasker.mm_gpu import run_mm_task_gpu
            mm_fn = run_mm_task_gpu
        else:
            import numpy as np
            from tasker.mm import run_mm_task
            mm_fn = run_mm_task

        import math
        arr_a = np.frombuffer(matrix_a_bytes, int)
        arr_b = np.frombuffer(matrix_b_bytes, int)
        # We are guaranteed to have square matrices for this evaluation.
        dim = int(math.sqrt(len(arr_a)))
        log.d('Matrices are {}x{}'.format(dim, dim))
        res = mm_fn(arr_a.reshape((dim, dim)),
                    arr_b.reshape((dim, dim))).tolist()

        res_data = run_mm_task(arr_a.reshape((dim, dim)),
                               arr_b.reshape((dim, dim))).tobytes()
    elif task_id < 30:
        # Additional data is the signal samples.
        import numpy as np
        samples = np.frombuffer(additional_data)
        res_data = run_fft_task(samples).tobytes()
    else:
        print(f'ERROR: task_id {task_id} is undefined')
    end_time = time.time()

    log.i(f'offload_id={task_request["offload_id"]}. completed executing task. time={(time.time() - start_time)*1000}')

    # Collect current state and send it, along with the result.
    current_state = stats.fetch()
    response_json = json.dumps({
        'executor_id': task_request['executer_id'],
        'task_id': task_request['task_id'],
        'offload_id': task_request['offload_id'],
        'state': current_state,
        'energy': power * (end_time - start_time),
        'status': 0
    })
    response_data = flserialize.pack(response_json, res_data)

    pipe.send(response_data)
    pipe.close()
