from functools import partial
import json
import socketserver
from http.server import BaseHTTPRequestHandler
from classes.task import Task
from queue import Queue
from threading import Thread
import cgi
import flomqtt.serialize as flserialize
import threading
import time

PORT = 8001
DEFAULT_DEADLINE = 15000  # 15 seconds

class MyHTTPRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, server_state, *args, **kwargs):
        self.server_state = server_state

        # BaseHTTPRequestHandler calls do_GET **inside** __init__ !!!
        # So we have to call super().__init__ after setting attributes.
        super().__init__(*args, **kwargs)

    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def log_message(self, format, *args):
        pass

    def do_POST(self):
        if self.path == '/submit-task':
            # receive the task parameters
            ctype, pdict = cgi.parse_header(self.headers['content-type'])

            # refuse to receive non octet-stream content
            if ctype != 'application/octet-stream':
                self.send_response(400)
                self.end_headers()
                return

            # read the message and convert it into a python dictionary
            length = int(self.headers['content-length'])
            post_input_data = self.rfile.read(length)

            (task_json, additional_data) = flserialize.unpack(post_input_data)
            task_request = json.loads(task_json)
            task_request['input_data'] = additional_data

            # do some sanity checks
            fields = task_request.keys()
            if "device_id" not in fields or "task_id" not in fields or "input_data" not in fields:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                response = "ERROR: some of these fields seem to be missing: device_id, task_id, input_data"
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            # if everything proper, assign a new unique task id to it and send it as response
            offload_id = self.server_state.get_next_offload_id()
            self._set_response()
            response = {
                "offload_id": offload_id
            }

            # send the unique offloaded_task_id back as response
            self.wfile.write(json.dumps(response).encode('utf-8'))

            # send the task to the task dispatcher
            device_id = task_request["device_id"]
            task_id = task_request["task_id"]
            input_data = task_request["input_data"]
            deadline = task_request["deadline"] if "deadline" in fields else DEFAULT_DEADLINE
            job_id = task_request["job_id"] if "job_id" in task_request else None
            schedule_on_executor = task_request[
                "schedule_on_executor"] if "schedule_on_executor" in task_request else None

            task = Task(offload_id, task_id, device_id, input_data, deadline, job_id, schedule_on_executor)
            self.server_state.enqueue_task(task)

            del post_input_data

        elif self.path == '/submit-img-classification-task':
            # receive the task parameters
            ctype, pdict = cgi.parse_header(self.headers['content-type'])

            # refuse to receive non octet-stream content
            if ctype != 'application/octet-stream':
                self.send_response(400)
                self.end_headers()
                return

            # read the message and convert it into a python dictionary
            length = int(self.headers['content-length'])
            post_input_data = self.rfile.read(length)

            task_request = {'device_id': 0,
                            'task_id': 49,
                            'job_id': 0,
                            'schedule_on_executor': 0,
                            'deadline': 140.11 * (49 - 40) + 7017.53,
                            'input_data': post_input_data}

            # do some sanity checks
            fields = task_request.keys()
            if "device_id" not in fields or "task_id" not in fields or "input_data" not in fields:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                response = "ERROR: some of these fields seem to be missing: device_id, task_id, input_data"
                self.wfile.write(json.dumps(response).encode('utf-8'))
                return

            # if everything proper, assign a new unique task id to it and send it as response
            offload_id = self.server_state.get_next_offload_id()
            self._set_response()
            response = {
                "offload_id": offload_id
            }

            # send the unique offloaded_task_id back as response
            self.wfile.write(json.dumps(response).encode('utf-8'))

            # send the task to the task dispatcher
            device_id = task_request["device_id"]
            task_id = task_request["task_id"]
            input_data = task_request["input_data"]
            deadline = task_request["deadline"] if "deadline" in fields else DEFAULT_DEADLINE
            job_id = task_request["job_id"] if "job_id" in task_request else None
            schedule_on_executor = task_request[
                "schedule_on_executor"] if "schedule_on_executor" in task_request else None

            task = Task(offload_id, task_id, device_id, input_data, deadline, job_id, schedule_on_executor)
            self.server_state.enqueue_task(task)

            del post_input_data
        else:
            self.send_response(404)

class ServerState:
    def __init__(self, task_dispatcher):
        self.task_dispatcher = task_dispatcher

        # Asynchronous task queueing and submission.
        self.__task_queue = Queue()
        self.__task_queue_cv = threading.Condition(lock=threading.Lock())

        self.__task_dispatch_thread = threading.Thread(
            target=async_task_dispatch_main,
            name='task-dispatch',
            args=(task_dispatcher,
                  self.__task_queue,
                  self.__task_queue_cv,))
        self.__task_dispatch_thread.start()

        # Offload ID handling.
        self.__next_offload_id = 0
        self.__next_offload_id_lock = threading.Lock()

    def get_next_offload_id(self):
        '''Return the next available offload ID.
        '''

        self.__next_offload_id_lock.acquire()
        offload_id = self.__next_offload_id
        self.__next_offload_id += 1
        self.__next_offload_id_lock.release()

        return offload_id

    def enqueue_task(self, task):
        '''Send a task to the dispatch queue.
        '''

        self.__task_queue_cv.acquire()
        self.__task_queue.put(task)
        self.__task_queue_cv.notify()
        self.__task_queue_cv.release()

class ControllerServer:
    def __init__(self, task_dispatcher):
        self.state = ServerState(task_dispatcher)

    def start_server(self):
        # use partial application to pass task_dispatcher object to MyHTTPRequestHandler.
        # ref: https://stackoverflow.com/a/52046062
        handler = partial(MyHTTPRequestHandler, self.state)

        while True:
            try:
                print('[server] starting with HTTP server on port {}'.format(PORT))
                with socketserver.TCPServer(("", PORT), handler) as httpd:
                    print("[server] started serving at port", PORT)
                    httpd.serve_forever()

            except OSError as e:
                print('[server] binding failed; waiting 30 secs.')
                time.sleep(30)

def async_task_dispatch_main(task_dispatcher, task_queue, task_queue_cv):
    '''Send task submissions to the task dispatcher asynchronously.
    '''

    print('[tda] started')
    local_task_queue = Queue()

    while True:
        task_queue_cv.acquire()
        while task_queue.empty():
            task_queue_cv.wait()

        # This is the only thread dequeueing tasks; there will always be a task to dequeue.
        # Move tasks to the local queue.
        while not task_queue.empty():
            local_task_queue.put(task_queue.get())
        task_queue_cv.release()

        # Process the local task queue while not holding the lock,
        # in case it takes a while.
        while not local_task_queue.empty():
            # This should never throw and exception because we check the queue state just prior.
            dequeued_task = local_task_queue.get(block=False)
            print('[tda] submitting offload_id={} to task dispatcher'.format(dequeued_task.offload_id))
            task_dispatcher.submit_task(dequeued_task)
