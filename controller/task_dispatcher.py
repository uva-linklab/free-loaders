from threading import Thread
import paho.mqtt.client as mqtt
import json
import asyncio
from aiohttp import ClientSession
import time
import flomqtt.serialize as flserialize

executer_server_port = 8088

# mqtt topics
controller_offloader_task_response_topic = "ctrl-offl-task-response"  # pub

controller_offloader_feedback_request_topic = "ctrl-offl-feedback-request"  # pub
offloader_controller_feedback_response_topic = "offl-ctrl-feedback-response"  # sub

controller_executer_task_execute_topic = "ctrl-exec-task-execute"  # pub
executer_controller_task_response_topic = "exec-ctrl-task-response"  # sub


# TODO update
def request_feedback(self, task_id, feedback):
    pass


async def fetch_json(executer_id: int, url: str, session: ClientSession, **kwargs) -> tuple:
    resp = await session.request(method="GET", url=url, **kwargs)
    response_json = await resp.json()
    return executer_id, response_json


async def make_requests(url_tuples: list, **kwargs) -> None:
    async with ClientSession() as session:
        tasks = []
        for url_tuple in url_tuples:
            tasks.append(
                fetch_json(executer_id=url_tuple[0], url=url_tuple[1], session=session, **kwargs)
            )
        results = await asyncio.gather(*tasks)

    return results


class TaskDispatcher:
    def __init__(self, rl_scheduler, executers):
        self.rl_scheduler = rl_scheduler
        self.executers = executers
        self.mqtt_client = mqtt.Client(client_id="fl-controller", clean_session=False)
        self.execution_times = {}  # offload_id -> start_time
        self.deadlines = {}  # offload_id -> deadline
        self.deadlines_met = 0
        self.finished_tasks = 0
        self.failed_tasks = 0
        self.total_tasks = 0

        # The callback for when the client receives a CONNACK response from the server.
        clientloop_thread = Thread(target=self.connect, args=(self.mqtt_client,))
        clientloop_thread.start()

        # initialize the rl scheduler's feedback consumer thread
        Thread(target=rl_scheduler.feedback_consumer).start()



    def on_connect(self, client, userdata, flags, rc):
        print("[td] connected to mqtt with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(offloader_controller_feedback_response_topic, qos=2)
        client.subscribe(executer_controller_task_response_topic, qos=2)

    def on_message(self, client, userdata, mqtt_message):
        # mqtt_message is of type MQTTMessage. Has fields topic, payload,..
        topic = mqtt_message.topic
        payload = mqtt_message.payload

        try:
            # We are not actually using _data here.
            (message_json, _data) = flserialize.unpack(payload)
            message_json = json.loads(message_json)
            print(f'[td] new mqtt message! response for offload_id={message_json["offload_id"]}')
        except Exception as e:
            import traceback
            print(f"[td] hit exception in mqtt json parse")
            print(e)
            print(payload)
            traceback.print_exception(type(e), e, e.__traceback__)
        else:
            if topic == offloader_controller_feedback_response_topic:
                pass
            elif topic == executer_controller_task_response_topic:
                # get the response
                offload_id = message_json["offload_id"]
                state_of_executor = message_json["state"]
                executor_id = message_json["executor_id"]
                task_id = message_json["task_id"]
                status = message_json["status"]
                energy = message_json["energy"]

                if offload_id not in self.execution_times.keys():
                    # ignore a response if we're not expecting it
                    print(f"[td] ignored response for task (offload_id={offload_id}, task_id={task_id}) from executer_id={executor_id}")
                    return

                # compute execution time
                exec_time_ms = (time.time() - self.execution_times[offload_id]) * 1000
                deadline = self.deadlines[offload_id]

                if status != 0:
                    # execution failed to finish
                    print(f"[td] failed task(offload_id={offload_id}, task_id={task_id}) on executer_id={executor_id}, status={status}. deadline={deadline}, deadline_met={False}")
                    self.failed_tasks += 1
                else:
                    print(f"[td] finished task(offload_id={offload_id}, task_id={task_id}) on executer_id={executor_id}."
                          f" time(ms)={exec_time_ms}, deadline={deadline}, deadline_met={exec_time_ms <= deadline},"
                          f" energy={energy}")
                    self.finished_tasks += 1
                    deadline_met = exec_time_ms <= deadline
                    self.deadlines_met += (1 if deadline_met else 0)

                dsr = self.deadlines_met/(self.finished_tasks+self.failed_tasks)
                print(f"[td] deadlines_met={self.deadlines_met}, finished_tasks={self.finished_tasks}, failed_tasks={self.failed_tasks}, pending_tasks={self.total_tasks-(self.finished_tasks+self.failed_tasks)}, dsr={dsr}")

                # # give the feedback to the rl scheduler
                # TODO update energy consumption
                self.rl_scheduler.feedback_q.put({
                    "offload_id": offload_id,
                    "exec_id": str(executor_id),
                    "status": status,
                    "exec_time": exec_time_ms,
                    "energy": energy,
                    "new_state_of_executor": state_of_executor
                })

                del message_json["state"] # exclude state from being sent to the offloader
                # publish this to the offloader
                client.publish(controller_offloader_task_response_topic,
                               json.dumps(message_json).encode('utf-8'),
                               qos=2)

                # remove the offload_id's execution time and deadline from memory
                del self.execution_times[offload_id]
                del self.deadlines[offload_id]

                print(f"[td] pending task offload_ids: {self.execution_times.keys()}")


    def on_disconnect(self, client, userdata, rc=0):
        print("DisConnected result code " + str(rc))
        client.loop_stop()

    def connect(self, mqtt_client):
        mqtt_client.on_connect = self.on_connect
        mqtt_client.on_message = self.on_message
        mqtt_client.on_disconnect = self.on_disconnect

        mqtt_client.connect("localhost", 1883, 60)
        mqtt_client.loop_forever()

    def on_publish(self, client,userdata,result):
        print("data published \n")

    def send_task_to_executer(self, executer_id, task):
        # publish on mqtt to executer
        # assumption: each executer knows its id
        task_json = json.dumps({
            "executer_id": executer_id,
            "offload_id": task.offload_id,
            "task_id": task.task_id,
        })

        import struct
        import numpy as np
        mqtt_message = b''
        # Define a consistent byte order.
        adt = np.dtype('<i4')

        if task.task_id < 10:
            # Loop task. Place the value as the input data.
            mqtt_message = flserialize.pack(task_json, struct.pack('I', task.input_data))
        elif task.task_id < 20:
            # Matrix multiplication.
            import numpy as np
            # Input data are lists of lists of integers.
            # Create the numpy array from that, turn it into bytes.
            m1_bytes = np.array(task.input_data['a'], dtype=adt).tobytes()
            m2_bytes = np.array(task.input_data['b'], dtype=adt).tobytes()
            # Serialize the numpy arrays, placing the length of the first matrix as the first piece of data.
            payload = struct.pack('I', len(m1_bytes)) + m1_bytes + m2_bytes
            mqtt_message = flserialize.pack(task_json, payload)
        elif task.task_id < 30:
            # FFT.
            import numpy as np
            # Input data is a list of floats.
            # Create the numpy array from that, turn it into bytes.
            arr_bytes = np.array(task.input_data, dtype=adt).tobytes()
            mqtt_message = flserialize.pack(task_json, arr_bytes)
        else:
            print('bad task ID: {}'.format(task.task_id))

        executor_topic = f'{controller_executer_task_execute_topic}-{executer_id}'

        self.mqtt_client.publish(executor_topic,
                                 mqtt_message,
                                 qos=2)

        print(f'published to {executor_topic}')

    def get_executer_state(self):
        # create a list of all executer ips with a specific http endpoint
        executer_items = list(self.executers.items())
        url_tuples = list(map(lambda item: (str(item[0]), f'http://{item[1].executer_ip}:{executer_server_port}/state'), executer_items))
        return dict(asyncio.run(make_requests(url_tuples=url_tuples)))

    def submit_task(self, task):
        print(f"[td] new task(offload_id={task.offload_id}, task_id={task.task_id}, deadline={task.deadline})")

        self.execution_times[task.offload_id] = time.time()
        self.deadlines[task.offload_id] = task.deadline

        # query all executers for their state
        state_of_executors = self.get_executer_state()

        #print(f'[td] before_state = {state_of_executors}')

        # request rl scheduler to schedule this task
        executer_id = self.rl_scheduler.schedule(state_of_executors, task)

        print(f"[td] scheduled task(offload_id={task.offload_id}, task_id={task.task_id}) on executer_id={executer_id}")

        self.send_task_to_executer(executer_id, task)

        self.total_tasks += 1
