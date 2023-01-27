import argparse
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='Output file path.',
                type=str, dest='output', default='dsr-offloads.pdf')
ap.add_argument('--window-size', help='Number of samples in a window',
                type=int, dest='window', default=100)
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=0)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('path', help='path to log file',
                type=str)

args = ap.parse_args()

log_lines = ''
with open(args.path, 'r') as fh:
    log_lines = fh.readlines()

r = 'deadlines_met=(?P<met>\d+).*finished_tasks=(?P<finished>\d+).*failed_tasks=(?P<failed>\d+)'
x = [0]
y = [1]
last_met = 0
dsr_window = []
for line in log_lines:
    m = re.search(r, line)
    if m == None:
        continue

    met = int(m['met'])
    finished = int(m['finished'])
    failed = int(m['failed'])

    if finished < args.start:
        continue
    elif args.end != None and finished > args.end:
        break

    if met > last_met:
        dsr_window.append(1)
    else:
        dsr_window.append(0)

    x.append(finished)
    if len(dsr_window) >= args.window:
        dsr_window = dsr_window[1:]

    y.append(sum(dsr_window) / len(dsr_window))

    last_met = met

plt.plot(x, y)

# Find out where executors 8 and 9 get used again.
found_8 = False
found_9 = False
r = 'scheduled task\(offload_id=(?P<oid>\d+).*on executer_id=(?P<eid>\d+)\.'
for line in log_lines:
    m = re.search(r, line)
    if m == None:
        continue

    eid = int(m['eid'])
    oid = int(m['oid'])

    if oid < 500:
        continue

    if (not found_8) and oid == 8:
        found_8 = True
        plt.annotate('begins using executor 8',
                     xy=(oid, y[oid]), xytext=(oid+1, y[oid]+.5),
                     arrowprops=dict(facecolor='black', shrink=0.05))

    if (not found_9) and oid == 9:
        found_9 = True
        plt.annotate('begins using executor 9',
                     xy=(oid, y[oid]), xytext=(oid+1, y[oid]+.5),
                     arrowprops=dict(facecolor='black', shrink=0.05))

    if found_8 and found_9:
        break

# plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Deadline satisfaction ratio')
plt.xlim(0, x[-1])
plt.ylim(0, 1)
plt.grid()
plt.savefig(args.output, format='pdf', dpi='figure', pad_inches=0.1)
