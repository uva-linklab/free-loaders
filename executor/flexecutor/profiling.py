import os
import os.path
import sys
from enum import Enum

import log

class ProfilingState(Enum):
    PEND = 1
    DONE = 2

# Path to Linux perf utility.
# Check the environment variable in case it is set.
# Otherwise, assume it is at /usr/bin/perf
_PerfPath = os.getenv('PERF_PATH', default='/usr/bin/perf')
# Check that it exists.
if not os.path.isfile(_PerfPath):
    print('perf does not exist at {}'.format(_PerfPath))
    sys.exit(1)

_TaskProfilingData = {}

def get_profiling_data(task_id):
    '''Return stored profiling data.
    '''

    global _TaskProfilingData

    if task_id not in _TaskProfilingData.keys():
        # Start profiling in a separate thread.
        profile(task_id)
        return (ProfilingState.PEND, None,)
    else:
        return _TaskProfilingData[task_id]

def profile(task_id):
    '''Trigger profiling for a task.
    '''

    import threading

    t = threading.Thread(name='profiler-task-{}'.format(task_id),
                         target=_profile_task_entry,
                         args=(task_id,))
    t.start()

def _profile_task_entry(task_id):
    '''Profile a task and store results.
    '''

    global _TaskProfilingData

    log.i('Profiling task {}'.format(task_id))

    script_path = os.path.join(os.getenv('HOME'), 'free-loaders')
    script_args = []
    if task_id < 10:
        script_path = os.path.join(
            script_path,
            'executor/flexecutor/tasker/loop.py')
        script_args.extend([str((task_id + 1) * 1000000)])
    elif task_id < 20:
        script_path = os.path.join(
            script_path,
            'executor/flexecutor/tasker/mm.py')
        script_args.extend([str(500 + math.ceil((task_id - 10) * 55.5))])
    elif task_id < 30:
        script_path = os.path.join(
            script_path,
            'executor/flexecutor/tasker/fft.py')
        script_args.extend([str(44100 * (task_id - 19) * 3)])
    elif task_id < 40:
        script_path = os.path.join(
            script_path,
            'executor/flexecutor/tasker/har/human_act_rec.py')
        script_args.extend([str(task_id - 30 + 1)])
    elif task_id < 50:
        input_path = os.path.join(
            script_path,
            'mock-offloader/moffloader/obj_det_input_files',
            'dog{}.jpg'.format(task_id - 40))
        script_path = os.path.join(
            script_path,
            'executor/flexecutor/tasker/obj_detection.py')
        script_args.extend([input_path])
    elif task_id < 60:
        input_path = os.path.join(
            script_path,
            'mock-offloader/moffloaders/room_classification_input_files',
            'room{}.jpg'.format(task_id - 50))
        script_path = os.path.join(
            script_path,
            'executor/flexecutor/tasker/room_classification/room_classification.py')
        script_args.extend([input_path])

    import subprocess
    cli = [_PerfPath, 'stat',
           'python',
           script_path]
    cli.extend(script_args)
    log.i('Launching: {}'.format(cli))
    r = subprocess.run(cli, capture_output=True)

    if r.returncode != 0:
        log.e('Profiling task {} failed.\nSTDOUT: {}\nSTDERR: {}'.format(
            task_id, r.stdout, r.stderr))
        return

    (ins_count, mips,) = _extract_perf_stats(r.stderr)
    log.i('Profiling task {} done: ({} ins. @ {} MIPS)'.format(
        task_id, ins_count, mips))

    _TaskProfilingData[task_id] = (ProfilingState.DONE, (ins_count, mips,),)

def _extract_perf_stats(output):
    '''Parse perf output for CPU instruction count.
    '''

    import re

    lines = output.decode().strip().split('\n')
    ins_line = lines[7]
    time_line = lines[11]

    # Extract instruction count from output.
    m = re.search('(?P<ins>[0-9,]+) +instructions', ins_line)
    ins_count = int(m['ins'].replace(',', ''))

    # Calculate MIPS from timing.
    m = re.search('(?P<t>[0-9.]+) +seconds time elapsed', time_line)
    time_elapsed = float(m['t'])
    mips = ins_count * (1.0 / time_elapsed) / 1000000

    return (ins_count, mips,)
