import argparse
import re

import matplotlib.pyplot as plt
import numpy

class Task:
    def __init__(self, oid, eid, extime, deadline, success):
        self.oid = oid
        self.eid = eid
        self.execution_time = extime
        self.deadline = deadline
        self.success = success

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='Output file path.',
                type=str, dest='output', default='dsr-offline-online-offloads.pdf')
ap.add_argument('--window-size', help='Number of samples in a window',
                type=int, dest='window', default=300)
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=0)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('--omit-range', help='Range of offloads to leave out',
                type=str, dest='omit_range', default=None)
ap.add_argument('-f', '--initial-window', help='Assume a perfect initial DSR window',
                dest='initial_window', action='store_true', default=False)
ap.add_argument('path', help='path to log file',
                type=str)

args = ap.parse_args()

omit_range = []
if args.omit_range != None:
    for r in args.omit_range.split(','):
        spl = r.split('-')
        omit_range.append((int(spl[0]), int(spl[1])))

log_lines = ''
with open(args.path, 'r') as fh:
    log_lines = fh.readlines()

# Get information on all offloads: OID, EID, executor, outcome, etc.
# rx_scheduled = 'scheduled task\(offload_id=(?P<oid>\d+).*on executer_id=(?P<eid>\d+)'
rgx_failed_task = 'failed task\(offload_id=(?P<oid>\d+).*on executer_id=(?P<eid>\d+).*deadline=(?P<dl>\d+\.\d+)'
rgx_finished_task = 'finished task\(offload_id=(?P<oid>\d+).*on executer_id=(?P<eid>\d+).*time\(ms\)=(?P<time>\d+\.\d+).*deadline=(?P<dl>\d+\.\d+)'
offloads = {}
for line in log_lines:
    task = None
    skip = False

    m = re.search(rgx_finished_task, line)
    if m != None:
        oid = int(m['oid'])
        eid = int(m['eid'])
        execution_time = float(m['time'])
        deadline = float(m['dl'])

        offset = 0
        for r in omit_range:
            if oid >= r[0] and oid <= r[1]:
                skip = True
                continue

            if oid > r[1]:
                offset -= (r[1] - r[0])

        if skip == True:
            continue

        oid += offset

        offloads[oid] = Task(oid, eid, execution_time, deadline, True)

    else:
        m = re.search(rgx_failed_task, line)
        if m != None:
            oid = int(m['oid'])
            eid = int(m['eid'])
            deadline = float(m['dl'])

            offset = 0
            for r in omit_range:
                if oid >= r[0] and oid <= r[1]:
                    skip = True
                    continue

                if oid > r[1]:
                    offset -= r[1] - r[0]

            if skip == True:
                continue

            oid += offset

            offloads[oid] = Task(oid, eid, 0, deadline, False)

# Fill the initial DSR window.
dsr_window = [1 for _i in range(0, args.window)] if args.initial_window else []
# X and Y coordinates for points.
x = []
y = []
# Colors to use for each one.
c = []
success_color = [126 / 255, 229 / 255, 134 / 255] # Green
timeout_color = [252 / 255, 175 / 255, 93 / 255]  # Orange
failure_color = [229 / 255, 126 / 255, 127 / 255] # Red
# Process the offloads in order so the moving average DSR calculation is correct.
oids = list(offloads.keys())
oids.sort()
for oid in oids:
    if oid < args.start:
        continue
    elif args.end != None and oid > args.end:
        break

    task = offloads[oid]
    x.append(oid) # Offload ID is X.

    # Continue the DSR calculation.
    # Success means the task was completed successfully and the deadline was met.
    success = task.success and task.execution_time <= task.deadline
    dsr_window.append(1 if success else 0)
    if len(dsr_window) >= args.window:
        dsr_window = dsr_window[1:]
    dsr = sum(dsr_window) / len(dsr_window)
    y.append(dsr) # Average DSR is Y.

    # Color depends on success/failure and deadline met/miss.
    if task.success:
        if task.execution_time <= task.deadline:
            c.append(success_color)
        else:
            c.append(timeout_color)
    else:
        c.append(failure_color)

# Separate the successful offloads and the failed offloads.
# Having the failed offloads drawn second makes them easier to see.
fail_x = []
fail_y = []
time_x = []
time_y = []
succ_x = []
succ_y = []
for (x, y) in zip(x, y):
    if offloads[x].success:
        if offloads[x].execution_time <= offloads[x].deadline:
            succ_x.append(x)
            succ_y.append(y)
        else:
            time_x.append(x)
            time_y.append(y)
    else:
        fail_x.append(x)
        fail_y.append(y)

plt.scatter(succ_x, succ_y, s=0.2, color=success_color, marker='.', label='success')
plt.scatter(time_x, time_y, s=0.2, color=timeout_color, marker='.', label='deadline miss')
plt.scatter(fail_x, fail_y, s=0.2, color=failure_color, marker='.', label='execution failure')

plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Deadline satisfaction ratio')
plt.xlim(0, args.end if args.end != None else max(offloads.keys()))
plt.ylim(0, 1)
plt.grid()
plt.savefig(args.output, format='pdf', dpi='figure', pad_inches=0.1)
