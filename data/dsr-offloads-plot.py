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
ap.add_argument('--x-limit', help='Max offload no. to plot',
                dest='x_limit', type=int, action='store', default=None)
ap.add_argument('paths', help='label,path to log file',
                nargs='+', type=str)

args = ap.parse_args()

colors = [
    [242 / 255, 101 / 255, 82 / 255], # red
    [247 / 255, 172 / 255, 42 / 255], # orange
    [97 / 255, 188 / 255, 249 / 255], # blue
    [244 / 255, 234 / 255, 31 / 255], # yellow
]

r = 'deadlines_met=(?P<met>\d+).*finished_tasks=(?P<finished>\d+).*failed_tasks=(?P<failed>\d+)'
for (label_path, color) in zip(args.paths, colors):
    [label, path] = label_path.split(',')
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

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

    plt.plot(x, y, label=label, linewidth=1.0, color=color)

plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Deadline satisfaction ratio')
plt.xlim(0, x[-1] if args.x_limit == None else args.x_limit)
plt.ylim(0, 1)
plt.grid()
plt.savefig(args.output, format='pdf', dpi='figure', pad_inches=0.1)
