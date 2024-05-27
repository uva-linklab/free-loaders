import multiprocessing
import queue
import threading
import time

import log

__MessageQueue = queue.Queue()

def __loading_thread_main():
    global __MessageQueue

    log.i('loading thread started')
    active_processes = []

    while True:
        log.d('awaiting load message')
        msg = __MessageQueue.get()
        log.d('got load message: {}'.format(msg['profile']))

        if msg['profile'] == 'constant':
            import os

            per_core_unit_load = 1.0 / os.cpu_count()
            target = msg['target']
            whole_load_count = int(msg['target'] / per_core_unit_load)
            partial_load = round(msg['target'] % per_core_unit_load, 2)

            log.i('will start {} whole-load processes, partial at {}'.format(whole_load_count, partial_load))

            for i in range(0, whole_load_count):
                p = multiprocessing.Process(target=__whole_load_thread_main,
                                            args=())
                p.start()
                active_processes.append(p)

            # Start the partial load process.
            p = multiprocessing.Process(target=__partial_load_thread_main,
                                        args=(partial_load,))
            p.start()
            active_processes.append(p)

        elif msg['profile'] == 'intermittent':
            import os

            freq = msg['frequency']
            d_spike = msg['duration']

            # Pick a consistent time base for subordinate load processes to synchronize load spikes.
            t_base = time.time()
            for i in range(0, os.cpu_count()):
                p = multiprocessing.Process(target=__intermittent_load_thread_main,
                                            args=(freq, d_spike, t_base,))
                p.start()
                active_processes.append(p)

        elif msg['profile'] == 'none':
            log.d('killing {} load processes'.format(len(active_processes)))
            for p in active_processes:
                p.kill()

            active_processes.clear()

def __whole_load_thread_main():
    while True:
        pass

def __partial_load_thread_main(load):
    '''Generate partial CPU load.
    '''

    # Based on https://qxf2.com/blog/generate-cpu-load
    import math

    interval = .25 # What interval of time to subdivide into busy-idle cycles.
    while True:
        t_transition = time.time() + (interval * load)
        while time.time() < t_transition:
            a = math.sqrt(64 * 64 * 64 * 64)
        time.sleep(interval - (interval * load))

def __intermittent_load_thread_main(frequency, duration, t_base):
    '''Generate intermittent CPU load.

    Synchronize the times of processes with a common time base, t_base.
    Invariant: duration < frequency
    '''

    QuietDuration = frequency - duration

    # Based on https://qxf2.com/blog/generate-cpu-load
    import math

    t_next = t_base + QuietDuration
    while True:
        d_next_spike = t_next - time.time()
        time.sleep(d_next_spike)

        t_next_quiet = time.time() + duration
        while time.time() < t_next_quiet:
            math.sqrt(64 * 64 * 64 * 64 * 64)

        # Calculate the next spike.
        t_next += frequency


def start_loading_thread():
    '''Start the load thread.
    '''
    loading_thread = threading.Thread(name='loadgen',
                                      target=__loading_thread_main,
                                      args=())
    loading_thread.start()

    return loading_thread

def clear():
    '''Clear any load profile currently set.
    '''

    global __MessageQueue

    __MessageQueue.put({
        'profile': 'none',
    })

def set_constant_load(target):
    '''Set a constant load.
    '''

    global __MessageQueue

    __MessageQueue.put({
        'profile': 'constant',
        'target': target,
    })

def set_intermittent_load(frequency, duration):
    '''Set an intermittent load.
    '''

    global __MessageQueue

    __MessageQueue.put({
        'profile': 'intermittent',
        'frequency': frequency,
        'duration': duration,
    })
