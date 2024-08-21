import functools
import multiprocessing
import os
import re
import subprocess
import threading
import time

import psutil

import log

__ExecutorName = os.getenv('EXEC_NAME')
if __ExecutorName == None:
    raise Exception('EXEC_NAME environment variable not set.')

def start_cpu_monitor_thread():
    '''Starts a CPU load-monitoring thread.
    '''

    t = threading.Thread(name='cpu-monitor',
                         target=__cpu_load_entry)
    t.daemon = True
    t.start()

    return t

def start_gpu_monitor_thread():
    '''Starts a GPU-monitoring thread.
    '''

    t = threading.Thread(name='gpu-monitor',
                         target=__gpu_load_entry)
    t.daemon = True
    t.start()

    return t

def fetch():
    '''Returns a dictionary of system state information.

    Includes the following stats:
    - 1-min. CPU load
    - free RAM
    - total RAM installed
    - free VRAM
    - total VRAM
    - no. of processes
    - no. of threads
    '''

    # Get consistent views of these once.
    mem = psutil.virtual_memory()
    (proc_count, thread_count) = _process_thread_count()
    gpu_stats = _gpu_stats()

    # Fill in the VRAM stats if it is shared.
    if gpu_stats['free-vram'] == None:
        gpu_stats['free-vram'] = mem.available
        gpu_stats['total-vram'] = mem.total

    state = {
        'cpu-count': os.cpu_count(),
        # 'cpu-load': psutil.getloadavg()[0],
        'cpu-load': round(_cpu_stload(), 2),
        'free-ram': mem.available,
        'total-ram': mem.total,
        'has-gpu': gpu_stats['has-gpu'],
        'gpu-load': gpu_stats['load'],
        'free-vram': gpu_stats['free-vram'],
        'total-vram': gpu_stats['total-vram'],
        'process-count': proc_count,
        'thread-count': thread_count,
        'h': _selection_value(),
    }

    return state

def _process_thread_count():
    pids = psutil.pids()
    process_count = len(pids)
    thread_count = 0
    # Place process and thread count acquisition in a loop.
    # System state changes may keep psutil from getting information without error.
    while True:
        try:
            thread_count = functools.reduce(
                lambda acc, c: acc + c,
                map(lambda p: p.num_threads(),
                    psutil.process_iter()),
                0)
            break
        except (psutil.NoSuchProcess, FileNotFoundError):
            log.d('psutil failed to get process, thread count; retrying')
            time.sleep(.05)

    return (process_count, thread_count)

__CPULoads = [float(os.cpu_count())]
__CPULoadLock = multiprocessing.Lock()

def _cpu_stload():
    '''Return the short-term CPU load of the executor.
    '''

    global __CPULoads
    global __CPULoadLock

    __CPULoadLock.acquire(block=True)
    if len(__CPULoads) > 0:
        cpu_load = sum(__CPULoads) / float(len(__CPULoads))
    else:
        cpu_load = float(os.cpu_count())
    __CPULoadLock.release()

    return cpu_load

# Path to the NVIDIA SMI binary.
__NVIDIASMIPath = '/usr/bin/nvidia-smi'
# Path to the tegrastats binary.
__TegraStatsPath = '/usr/bin/tegrastats'

def _gpu_stats():
    '''Fetch GPU usage information, if available.

    Has special handling for NVIDIA Jetson SBCs.
    '''

    stats = {
        'has-gpu': 0,
        'load': 0,
        'free-vram': 0,
        'total-vram': 0,
    }

    # Look at the kernel build to tell if this is a Jetson SBC.
    if os.uname().release.endswith('-tegra'):
        stats['has-gpu'] = 1
        stats['load'] = _get_gpu_load()
        # Note: SoC shares RAM between CPU and GPU.
        # Use None to tell the caller that this is the same as RAM.
        stats['free-vram'] = None
        stats['total-vram'] = None
    elif os.path.exists(__NVIDIASMIPath):
        cp = subprocess.run([__NVIDIASMIPath], capture_output=True)
        m = re.search('(?P<free>[0-9]+)MiB */ * (?P<total>[0-9]+)MiB',
                      cp.stdout.decode('utf-8'),
                      re.MULTILINE)

        if m != None:
            stats['has-gpu'] = 1
            stats['load'] = _get_gpu_load()
            stats['total-vram'] = int(m['total']) * 1024 * 1024
            stats['free-vram'] = stats['total-vram'] - (int(m['free']) * 1024 * 1024)

    return stats

def __cpu_load_entry():
    '''Entry point for CPU monitoring thread.
    '''

    global __CPULoads
    global __CPULoadLock

    log.i('started')

    target_sample_count = 20
    load_history_secs = 5
    sample_interval = load_history_secs / target_sample_count

    while True:
        current_usage = psutil.cpu_percent() / 100 * psutil.cpu_count()

        __CPULoadLock.acquire(block=True)
        __CPULoads.append(current_usage)
        while len(__CPULoads) > target_sample_count:
            __CPULoads = __CPULoads[1:]
        __CPULoadLock.release()
        time.sleep(sample_interval)

__GPULoad = 0
__GPULoadCollectInterval = .25
__GPULoadHistory = 60 / __GPULoadCollectInterval
__GPUUsagesCollected = 0.0
__GPULoadLock = multiprocessing.Lock()

def __gpu_load_entry():
    '''Entry point for GPU monitoring thread.
    '''

    global __GPULoad
    global __GPULoadHistory
    global __GPUUsagesCollected
    global __GPULoadLock

    log.i('started')

    # Jetson SBCs
    if os.uname().release.endswith('-tegra'):
        counter = 0
        max_util = 0
        # Start tegrastats as a subprocess.
        cmd = [__TegraStatsPath, '--interval', str(100)]
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, encoding='utf-8') as tegrastats_proc:
            # Collect load information.
            while True:
                output_line = tegrastats_proc.stdout.readline()
                m = re.search('GR3D_FREQ (?P<utilization>[0-9]{1,2})%', output_line)
                if m != None:
                    if max_util < int(m['utilization']):
                        max_util = int(m['utilization'])
                    counter = counter + 100
                    if counter / 1000.0 > __GPULoadCollectInterval:
                        counter = 0
                    else:
                        continue

                    current_gpu_usage = max_util / 100
                    max_util = 0

                    if __GPUUsagesCollected < __GPULoadHistory:
                        __GPUUsagesCollected = __GPUUsagesCollected + 1

                    if __GPULoadLock.acquire(block=True, timeout=2) == True:
                        if __GPUUsagesCollected == 1:
                            __GPULoad = current_gpu_usage
                        else:
                            __GPULoad = (__GPULoad * (__GPUUsagesCollected - 1) / __GPUUsagesCollected) + (current_gpu_usage * (1.0 / __GPULoadHistory))
                        __GPULoadLock.release()
                    else:
                        log.e('unable to acquire GPU load lock; continuing')
                else:
                    log.e('unable to collect GPU load data (line: "{}")'.format(output_line))
                    return

    # NVIDIA GPU-equipped computers
    elif os.path.exists(__NVIDIASMIPath):
        # Use NVIDIA SMI utility to get GPU information.
        log.i('Using nvidia-smi to get GPU information')
        nvidia_smi_args = [__NVIDIASMIPath, '-q', '-d', 'UTILIZATION']

        while True:
            cp = subprocess.run(nvidia_smi_args, capture_output=True)
            m = re.search('Gpu *: *(?P<utilization>[0-9][0-9]*) %', cp.stdout.decode('utf-8'), re.MULTILINE)
            if m == None:
                log.e('could not parse nvidia-smi output')
                # print(cp.stdout.decode('utf-8'))
            else:
                current_load = int(m['utilization']) / 100
                # log.d('current GPU load: {}'.format(current_load))
                if __GPUUsagesCollected < __GPULoadHistory / 4:
                    __GPUUsagesCollected = __GPUUsagesCollected + 1

                __GPULoadLock.acquire()
                if __GPUUsagesCollected == 1:
                    __GPULoad = current_load
                else:
                    __GPULoad = (__GPULoad * (__GPUUsagesCollected - 1) / __GPUUsagesCollected) + (current_load * (1.0 / __GPULoadHistory))
                    if __GPULoad < 0.0001:
                        __GPULoad = 0.0
                    # log.d('updated GPU load')

                # log.d('load: {}'.format(__GPULoad))
                __GPULoadLock.release()
            time.sleep(__GPULoadCollectInterval * 4)
    else:
        log.i('GPU monitor exiting because nothing to monitor')
        return

def _get_gpu_load():
    '''Returns the value for GPU load.
    '''

    global __GPULoad
    global __GPULoadLock
    __GPULoadLock.acquire()
    l = __GPULoad
    __GPULoadLock.release()

    return l

MIPSTable = {
    'rpi3':    1137.11,
    'rpi4':    2422.04,
    'nano':    3085.06,
    'tx2':     4140.84,
    'dellxps': 15274.47,
}

PowerTables = {
    'rpi3': [
        (0, 1.43),
        (1, 2.66),
        (1.25, 3.19),
        (1.5, 3.33),
        (1.75, 2.53),
        (2.0, 3.55),
        (2.5, 3.66),
        (3.0, 4.22),
        (4.0, 4.69)
    ],

    'rpi4': [
        (0, 2.9),
        (1, 3.66),
        (1.25, 3.77),
        (1.5, 3.94),
        (1.75, 4.17),
        (2.0, 4.32),
        (2.5, 4.56),
        (3.0, 4.68),
        (3.5, 4.84),
        (4.0, 5.14)
    ],

    'nano': [
        (0, 2.56),
        (1, 3.98),
        (1.25, 4.51),
        (1.5, 4.79),
        (1.75, 5.24),
        (2.0, 5.54),
        (2.5, 6.24),
        (3.0, 7.02),
        (3.5, 7.59),
        (4.0, 7.67)
    ],

    'tx2': [
        (0, 1.72),
        (1, 4.94),
        (1.25, 5.42),
        (1.5, 5.66),
        (1.75, 5.87),
        (2.0, 5.98),
        (2.5, 6.24),
        (3.0, 6.82),
        (3.5, 7.07),
        (4.0, 7.57),
        (5.0, 7.61),
        (6.0, 7.63),
    ],

    'dellxps': [
        (0, 38.7),
        (1, 61.64),
        (1.25, 71.27),
        (1.50, 76.4),
        (1.75, 78.44),
        (2.0, 79.55),
        (2.5, 87.5),
        (3.0, 94.28),
        (3.5, 101.67),
        (4.0, 112.98),
    ]
}

def _selection_value():
    '''Return the selection value for the given (non-unit) load.
    '''

    cpu_count = psutil.cpu_count(logical=False)
    is_hyperthreading = (psutil.cpu_count(logical=True) != psutil.cpu_count(logical=False))
    ht_factor = 2 if is_hyperthreading else 1
    # print('ht_factor = {}'.format(ht_factor))
    # print('cpu_count = {}'.format(cpu_count))
    current_load = _cpu_stload() * ht_factor * cpu_count
    # print('current_load = {}'.format(round(current_load, 2)))

    max_mips = MIPSTable[__ExecutorName]
    # Recommended parameters.
    g = 1.2
    a = 110
    b = 0.8

    import math

    current_power = __selection_power_value(current_load)
    # Assumption: the power-MIPS function of these executors is linear with increasing load,
    # which is not the case for all hardware.
    ppw_at_l = (max_mips * current_load) / current_power
    power_table = PowerTables[__ExecutorName]
    max_load = power_table[-1][0] # Load value of the last entry in the table.
    # print('max_load = {}'.format(max_load))

    h = ppw_at_l * (1 - (g / (1 + pow(math.e, -(a / max_load) * (current_load - (b * max_load))))))

    return h

def __selection_power_value(current_load):
    ptab = PowerTables[__ExecutorName]

    # If the load is greater than the number of cores, then we assume max load and power values.
    if current_load > os.cpu_count():
        return ptab[-1][1]
    else:
        # Find the closest power value not exceeding the load value.
        lower_power_bound = ptab[0][1]
        lower_load_bound = ptab[0][0]
        upper_power_bound = None
        upper_load_bound = None
        for ((lower_load, lower_power), (upper_load, upper_power)) in zip(ptab, ptab[1:]):
            if current_load >= lower_load:
                lower_power_bound = lower_power
                lower_load_bound = lower_load
                upper_power_bound = upper_power
                upper_load_bound = upper_load

        # Interpolate the current power value.
        load_range = upper_load_bound - lower_load_bound
        load_interpolation_x = current_load - lower_load_bound
        # What to multiply the range by to estimate current power.
        factor = load_interpolation_x / load_range
        # Add to the lower load a fraction of the range between the lower load bound
        # and the upper load bound to estimate where the current power draw is currently.
        power_range = upper_power_bound - lower_power_bound
        est_power = lower_power_bound + (power_range * factor)

        return est_power
