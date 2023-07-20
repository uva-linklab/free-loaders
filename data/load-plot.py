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
                type=str, dest='output', default='dsr-offloads.pdf')
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

loads = {i: [] for i in range(0, 10)}
for line in log_lines:
    if 'executor loads' not in line:
        continue

    # Get the load values in between the brackets.
    loads_s = (line.split('executor loads: ')[1])[1:-2]
    load_values_s = loads_s.split(',')
    executor_no = 0
    for v in load_values_s:
        load = float(v.lstrip().rstrip())
        loads[executor_no].append(load)
        executor_no += 1

for (executor_no, load_values) in loads.items():
    offload_no = 0
    offloads = []
    load = []
    for load_value in load_values:
        offloads.append(offload_no)
        load.append(load_value)
        offload_no += 1

    plt.plot(offloads, load, label = 'executor {} load'.format(executor_no))

plt.legend(title='Executors', fancybox=True, ncol=2)

plt.xlabel('offload no.')
plt.ylabel('load')
plt.xlim(0)
plt.ylim(0, 4)
plt.grid()
plt.savefig('/tmp/load.pdf', format='pdf', dpi='figure', pad_inches=0.1)
