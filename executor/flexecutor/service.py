import http.server
import json
import log
import random
import stats
import threading

import load
import profiling

HTTPServerPort = 8088

class ExecutorHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, request, client_addr, server):
        super().__init__(request, client_addr, server)

    def do_GET(self):
        log.i('{} GET {}'.format(self.client_address[0], self.path))

        if self.path == '/state':
            self.get_state()
        elif self.path.startswith('/profile/'):
            task_id = int(self.path.split('/')[-1])
            (profile_state, profile_data) = profiling.get_profiling_data(task_id)

            if profile_state == profiling.ProfilingState.PEND:
                self.send_response(102)
            else:
                j = json.dumps({
                    'ins_count': profile_data[0],
                    'mips': profile_data[1],
                })
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(j.encode('utf-8'))

        else:
            self.send_response(404)

    def do_POST(self):
        if self.path == '/load/clear':
            log.i('clearing load profile')
            load.clear()
            self.send_response(204)
            log.i('done setting load')
        elif self.path == '/load/set/constant':
            content = self.rfile.read(int(self.headers['content-length']))
            conf_json = json.loads(content)
            target_load = conf_json['load']

            log.i('setting load target of {}'.format(target_load))
            load.set_constant_load(target_load)
            log.i('done setting load')

            self.send_response(204)
        elif self.path == '/load/set/intermittent':
            content = self.rfile.read(int(self.headers['content-length']))
            conf_json = json.loads(content)

            freq = conf_json['frequency']
            d_spike = conf_json['duration']

            if d_spike >= freq:
                self.send_response(400)
            else:
                load.set_intermittent_load(freq, d_spike)
                self.send_response(204)

            log.i('done setting load')

        elif self.path == '/profile/clear':
            profiling.clear_profiling_data()

            self.send_response(204)
            log.i('cleared profiling data')

    def log_message(self, format, *args):
        pass

    def get_state(self):
        state = stats.fetch()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(state).encode('utf-8'))

class MaxedExecutorHTTPRequestHandler(ExecutorHTTPRequestHandler):
    def __init__(self, request, client_addr, server):
        super().__init__(request, client_addr, server)

    def get_state(self):
        state = stats.fetch()

        # Simulate a busy executor state.
        state['cpu-load'] = state['cpu-count'] + (random.randint(-10,99) / 100)
        state['process-count'] += 10
        state['thread-count'] += 20

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(state).encode('utf-8'))

def start_state_server(unavailable):
    log.i('Launching executor HTTP server.')
    t = threading.Thread(name='state-http-server',
                         target=__state_server_entry,
                         args=(unavailable,))
    t.daemon = True
    t.start()

    return t

def __state_server_entry(unavailable):
    listen_addr = ('', HTTPServerPort)

    server = None
    if unavailable:
        log.i('Maxed HTTP server starting on {}'.format(listen_addr))
        server = http.server.HTTPServer(listen_addr, MaxedExecutorHTTPRequestHandler)
    else:
        log.i('HTTP server starting on {}'.format(listen_addr))
        server = http.server.HTTPServer(listen_addr, ExecutorHTTPRequestHandler)

    server.serve_forever()
