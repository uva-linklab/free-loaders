import argparse
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='Output file path.',
                type=str, dest='output', default='dsr-offloads.pdf')
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=0)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('-w', '--window-size', help='Number of offloads in the averaging window',
                type=int, dest='window_size', default=100)
ap.add_argument('-f', '--initial-window', help='Assume a perfect initial DSR window',
                dest='initial_window', action='store_true', default=False)
ap.add_argument('--x-limit', help='Max offload no. to plot',
                dest='x_limit', type=int, action='store', default=None)
ap.add_argument('paths', help='label,path to log file',
                nargs='+', type=str)

args = ap.parse_args()

colors = {
    'fReeLoaders': [26 / 255, 121 / 255, 172 / 255],
    'load balancing': [28 / 255, 160 / 255, 63 / 255],
    'performance-WRR': [255 / 255, 124 / 255, 45 / 255],
    'random': [217 / 255, 28 / 255, 44 / 255],
}

r = 'finished task.*offload_id=(?P<oid>\d+), task_id=(?P<tid>\d+).*time\(ms\)=(?P<t>\d+\.\d+).*deadline=(?P<dl>\d+\.\d+)'
for (label_path, color) in zip(args.paths, range(0,10)):
    [label, path] = label_path.split(',')
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    x = []
    y = []
    rwin = [True for _i in range(0, args.window_size)]
    offset = 0
    last_met = 0
    for line in log_lines:
        m = re.search(r, line)
        if m == None:
            continue

        rwin.append(float(m['t']) < float(m['dl']))
        while len(rwin) > args.window_size:
            rwin = rwin[1:]

        dsr = len(list(filter(lambda b: b, rwin))) / args.window_size

        x.append(int(m['oid']))
        y.append(dsr)

    plt.plot(x, y, label=label, color=colors[label])

plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Deadline satisfaction ratio')
plt.xlim(0, x[-1] if args.x_limit == None else args.x_limit)
plt.ylim(0, 1)
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.grid()
plt.savefig(args.output, format='pdf', dpi='figure', pad_inches=0.1)
