import argparse
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='Output file path.',
                type=str, dest='output', default='dsr-offloads.pdf')
ap.add_argument('--window-size', help='Number of samples in a window',
                type=int, dest='window', default=300)
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=0)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('-f', '--initial-window', help='Assume a perfect initial DSR window',
                dest='initial_window', action='store_true', default=False)
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
dsr_window = [1 for _i in range(0,args.window)] if args.initial_window else []
for line in log_lines:
    m = re.search(r, line)
    if m == None:
        continue

    met = int(m['met'])
    finished = int(m['finished'])
    failed = int(m['failed'])
    processed = finished + failed

    if processed < args.start:
        continue
    elif args.end != None and processed > args.end:
        break

    if met > last_met:
        dsr_window.append(1)
    else:
        dsr_window.append(0)

    x.append(processed)
    if len(dsr_window) >= args.window:
        dsr_window = dsr_window[1:]

    dsr = sum(dsr_window) / len(dsr_window)
    y.append(dsr)

    last_met = met

plt.plot(x, y)

# plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Deadline satisfaction ratio')
plt.xlim(0, x[-1])
plt.ylim(0, 1)
plt.grid()
plt.savefig(args.output, format='pdf', dpi='figure', pad_inches=0.1)
