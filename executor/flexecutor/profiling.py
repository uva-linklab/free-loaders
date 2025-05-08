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

_TaskProfilingRounds = 1
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

    global _TaskProfilingData

    _TaskProfilingData[task_id] = (ProfilingState.PEND, None,)

    t = threading.Thread(name='profiler-task-{}'.format(task_id),
                         target=_profile_task_entry,
                         args=(task_id,))
    t.start()

def clear_profiling_data():
    '''Clear all profiling data.
    '''

    global _TaskProfilingData

    _TaskProfilingData = {}
    log.i('Cleared all profiling data.')

    return

def set_profiling_rounds(rounds):
    '''Set the number of rounds of profiling to determine task profile.
    '''

    global _TaskProfilingRounds
    _TaskProfilingRounds = rounds
    log.i(f'set profiling rounds to {rounds}')

def _profile_task_entry(task_id):
    '''Profile a task and store results.
    '''

    global _TaskProfilingData

    log.i('Profiling task {}'.format(task_id))

    fl_path = os.path.join(os.getenv('HOME'), 'free-loaders')
    python_path = os.path.join(os.getenv('VIRTUAL_ENV'), 'bin/python')
    script_path = os.path.join(os.getenv('HOME'), 'free-loaders')
    script_args = []

    if task_id < 10:
        script_path = os.path.join(
            script_path,
            'executor/flexecutor/tasker/loop.py')
        script_args.extend([str((task_id + 1) * 1000000)])
    elif task_id < 20:
        import math
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
            'mock-offloader/moffloader/room_classification_input_files',
            'room{}.jpg'.format(task_id - 50))
        script_path = os.path.join(
            script_path,
            'executor/flexecutor/tasker/room_classification/room_classification.py')
        script_args.extend([input_path])

    import subprocess

    global _TaskProfilingRounds
    wc_ins_count = None
    for _round_no in range(0, _TaskProfilingRounds):
        cli = ['pipenv', 'run',
               _PerfPath, 'stat',
               python_path,
               script_path]
        cli.extend(script_args)
        log.i('Launching: {}'.format(cli))
        r = subprocess.run(cli, capture_output=True, cwd=fl_path)

        if r.returncode != 0:
            log.e('Profiling task {} failed.\nSTDOUT: {}\nSTDERR: {}'.format(
                task_id, r.stdout, r.stderr))
            return

        (ins_count, mips,) = _extract_perf_stats(r.stderr)
        log.i(f'Task instruction count was {ins_count}')
        if wc_ins_count == None:
            wc_ins_count = ins_count
        else:
            wc_ins_count = max(wc_ins_count, ins_count)
            log.i(f'Worst task instruction count is now {wc_ins_count}')

    log.i('Profiling task {} done: ({} ins. @ {} MIPS)'.format(
        task_id, ins_count, mips))

    _TaskProfilingData[task_id] = (ProfilingState.DONE, (ins_count, mips,),)

def _extract_perf_stats(output):
    '''Parse perf output for CPU instruction count.
    '''

    import re

    lines = output.decode().strip().split('\n')
    ins_line = None
    time_line = None
    for ol in lines:
        if 'instructions' in ol:
            ins_line = ol
        elif 'seconds time elapsed' in ol:
            time_line = ol

    # Extract instruction count from output.
    m = re.search('(?P<ins>[0-9,]+) +instructions', ins_line)
    ins_count = int(m['ins'].replace(',', ''))

    # Calculate MIPS from timing.
    m = re.search('(?P<t>[0-9.]+) +seconds time elapsed', time_line)
    time_elapsed = float(m['t'])
    mips = ins_count * (1.0 / time_elapsed) / 1000000

    return (ins_count, mips,)
