from threading import Thread
import paho.mqtt.client as mqtt
import json
import asyncio
from aiohttp import ClientSession
from aiohttp import ClientTimeout
from aiohttp import ServerTimeoutError
import time
import flomqtt.serialize as flserialize
from threading import Timer
from schedulers.rl_scheduler import RLScheduler
import slt

executer_server_port = 8088

# mqtt topics
controller_offloader_task_response_topic = "ctrl-offl-task-response"  # pub

controller_offloader_feedback_request_topic = "ctrl-offl-feedback-request"  # pub
offloader_controller_feedback_response_topic = "offl-ctrl-feedback-response"  # sub

controller_executer_task_execute_topic = "ctrl-exec-task-execute"  # pub
executer_controller_task_response_topic = "exec-ctrl-task-response"  # sub

Assignments = {}

# TODO update
def request_feedback(self, task_id, feedback):
    pass


async def fetch_json(executer_id: int, url: str, session: ClientSession, **kwargs) -> tuple:
    resp = None
    while True:
        try:
            resp = await session.request(method="GET", url=url, **kwargs)
            break
        except:
            print('[td] error getting state from executor {}'.format(executer_id))
            time.sleep(0.5)
            continue

    response_json = await resp.json()

    return executer_id, response_json


async def make_requests(url_tuples: list, **kwargs) -> None:
    to = ClientTimeout(total=None, sock_connect=2)
    async with ClientSession(timeout=to) as session:
        tasks = []
        for url_tuple in url_tuples:
            tasks.append(
                fetch_json(executer_id=url_tuple[0], url=url_tuple[1], session=session, **kwargs)
            )
        results = await asyncio.gather(*tasks)

    return results


class TaskDispatcher:
    def __init__(self, scheduler, executers):
        self.scheduler = scheduler
        self.executers = executers
        self.mqtt_client = mqtt.Client(client_id="fl-controller", clean_session=False)
        self.execution_times = {}  # offload_id -> start_time
        self.deadlines = {}  # offload_id -> deadline
        self.timers = {}  # offload_id -> Timer
        self.deadlines_met = 0
        self.finished_tasks = 0
        self.failed_tasks = 0
        self.total_tasks = 0

        # The callback for when the client receives a CONNACK response from the server.
        clientloop_thread = Thread(target=self.connect, args=(self.mqtt_client,))
        clientloop_thread.start()

        # initialize the scheduler's feedback consumer thread
        if self.scheduler.needs_feedback:
            Thread(target=scheduler.feedback_consumer).start()

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
                # cancel timer for task offload_id
                self.handle_task_response(message_json["offload_id"],
                                          message_json["state"],
                                          message_json["executor_id"],
                                          message_json["task_id"],
                                          message_json["job_id"],
                                          message_json["status"],
                                          message_json["energy"])


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

    def handle_task_response(self,
                             offload_id,
                             state_of_executor,
                             executor_id,
                             task_id,
                             job_id,
                             status,
                             energy):
        if offload_id not in self.execution_times.keys():
            # ignore a response if we're not expecting it
            print(f"[td] ignored response for task (offload_id={offload_id}, task_id={task_id}) from executer_id={executor_id}")
            return

        # cancel timer
        self.timers[offload_id].cancel()
        print(f"[td] canceled timer for task (offload_id={offload_id}, task_id={task_id}) from executer_id={executor_id}")

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
        pending_task_count = len(self.execution_times.keys()) - 1 # -1 because this task just finished.
        print(f"[td] deadlines_met={self.deadlines_met}, finished_tasks={self.finished_tasks}, failed_tasks={self.failed_tasks}, pending_tasks={pending_task_count}, dsr={dsr}")

        # # give the feedback to the rl scheduler
        if self.scheduler.needs_feedback:
            if isinstance(self.scheduler, RLScheduler):
                del state_of_executor['h']

            self.scheduler.feedback_q.put({
                "offload_id": offload_id,
                "exec_id": str(executor_id),
                "task_id": task_id,
                "status": status,
                "exec_time": exec_time_ms,
                "energy": energy,
                "new_state_of_executor": state_of_executor
            })

        response = {
            "offload_id": offload_id,
            "executor_id": executor_id,
            "task_id": task_id,
            "job_id": job_id,
            "status": status,
            "energy": energy
        }

        # publish this to the offloader
        self.mqtt_client.publish(controller_offloader_task_response_topic,
                                 json.dumps(response).encode('utf-8'),
                                 qos=2)

        # remove the offload_id's execution time, deadline, and timer from memory
        del self.execution_times[offload_id]
        del self.deadlines[offload_id]
        del self.timers[offload_id]

        print('[td] pending (eid): {}'.format(['{} ({})'.format(k, Assignments.get(k, '?')) for k in self.execution_times.keys()]))
        #print(f"[td] pending task offload_ids: {self.execution_times.keys()}")

    def send_task_to_executer(self, executer_id, task):
        # publish on mqtt to executer
        # assumption: each executer knows its id
        task_json = json.dumps({
            "executer_id": executer_id,
            "offload_id": task.offload_id,
            "task_id": task.task_id,
            "job_id": task.job_id,
            "deadline": task.deadline
        })

        # task.input_data is already in bytes
        mqtt_message = flserialize.pack(task_json, task.input_data)
        print('[td] sending {} B (input size: {} B) for task {}'.format(len(mqtt_message), len(task.input_data), task.task_id))
        executor_topic = f'{controller_executer_task_execute_topic}-{executer_id}'

        self.mqtt_client.publish(executor_topic,
                                 mqtt_message,
                                 qos=2)

    def get_executer_state(self):
        # create a list of all executer ips with a specific http endpoint
        executer_items = list(self.executers.items())
        url_tuples = list(map(lambda item: (str(item[0]), f'http://{item[1].executer_ip}:{executer_server_port}/state'), executer_items))
        return dict(asyncio.run(make_requests(url_tuples=url_tuples)))

    def submit_task(self, task):
        print(f"[td] new task(offload_id={task.offload_id}, task_id={task.task_id}, job_id={task.job_id}, deadline={task.deadline})")

        self.execution_times[task.offload_id] = time.time()
        self.deadlines[task.offload_id] = task.deadline

        # query all executers for their state
        state_of_executors = None
        # only for the rl scheduler and the dynamic load based scheduler which need
        if self.scheduler.needs_before_state:
            #state_of_executors = self.get_executer_state()

            while True:
                try:
                    # Reassign start time to compensate fo the timeout and the wait.
                    self.execution_times[task.offload_id] = time.time()
                    # query all executers for their state
                    state_of_executors = self.get_executer_state()
                    break
                except ServerTimeoutError:
                    wait_time = 1
                    print('[td] timeout fetching state; retrying in {} second(s)'.format(wait_time))
                    time.sleep(wait_time)

            print('executor loads: {}'.format([state_of_executors[eid]['cpu-load'] for eid in sorted(list(state_of_executors.keys()))]))

            if isinstance(self.scheduler, RLScheduler):
                for value in state_of_executors.values():
                    del value['h']

        # request rl scheduler to schedule this task
        executer_id = self.scheduler.schedule(state_of_executors, task)
        Assignments[task.offload_id] = executer_id

        Thread(target=self.send_task_to_executer, args=(executer_id, task,)).start()

        state_of_executor = None if state_of_executors == None else state_of_executors[str(executer_id)]
        # timer to report failure if deadline elapses and executor is non-responsive
        # set to 10s after deadline (prefer failed response from executor, so wait for msg)
        self.timers[task.offload_id] = Timer((2 * task.deadline) / 1000 + 10,
                                             self.handle_task_response,
                                             args=[task.offload_id,
                                                   state_of_executor,
                                                   executer_id,
                                                   task.task_id,
                                                   task.job_id,
                                                   -1000,  # indicate failure
                                                   0.0])
        self.timers[task.offload_id].start()
        self.total_tasks += 1

        slt.update_load(task.offload_id, self.executers)
