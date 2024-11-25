import argparse
import os.path
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='Output file path.',
                type=str, dest='output', default='dsr-offloads-windowed.pdf')
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
ap.add_argument('--append-labels', help='Apply additional labeling to legend',
                dest='append_labels', type=str, action='store', default=None)
ap.add_argument('--date-runs', help='Append date labels to legends',
                dest='date_runs', action='store_true', default=False)

ap.add_argument('paths', help='path to log file',
                nargs='+', type=str)

args = ap.parse_args()

colors = {
    'rl': [[26 / 255, 121 / 255, 172 / 255],
           [137 / 255, 204 / 255, 240 / 255],
           [183 / 255, 218 / 255, 237 / 255]],
    'load-bal': [[199 / 255, 157 / 255, 250 / 255]],
    'random': [[217 / 255, 28 / 255, 44 / 255]],
    'time-wrr': [[252 / 255, 186 / 255,   3 / 255]],
    'heros': [[111 / 255, 166 / 255, 17 / 255],
              [170 / 255, 227 / 255, 73 / 255]],
    'adpt-lb-v1': [[200 / 255, 200 / 255, 200 / 255]],
    'adpt-lb-v3': [[25 / 255, 25 / 255, 25 / 255]],
}

pretty_names = {
    'rl': 'fReeLoaders',
    'load-bal': 'load balancer',
    'random': 'random',
    'time-wrr': 'performance-WRR',
    'heros': 'HEROS',
    'adpt-lb-v1': 'energy-priority',
    'adpt-lb-v3': 'performance-priority',
}

def which_scheduler(log):
    scheduler_name = None
    r = 'using (?P<sched>[a-z0-9-]+) scheduler'
    for line in log:
        m = re.search(r, line)
        if m != None:
            scheduler_name = m['sched']
            break

    return scheduler_name

r_finish = 'finished task.*offload_id=(?P<oid>\d+), task_id=(?P<tid>\d+).*time\(ms\)=(?P<t>\d+\.\d+).*deadline=(?P<dl>\d+\.\d+)'
r_failed = 'failed task.*offload_id=(?P<oid>\d+), task_id=(?P<tid>\d+)'
x_limit = 0
plotted = []
add_labels = args.append_labels.split(',') if args.append_labels != None else None
for (path, color) in zip(args.paths, range(0,10)):
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    label = which_scheduler(log_lines)

    x = []
    y = []
    rwin = [True for _i in range(0, args.window_size)] if args.initial_window else []
    offset = 0
    last_met = 0
    for line in log_lines:
        oid = None
        t = None
        dl = None

        matched = False
        m = re.search(r_finish, line)
        if m != None:
            matched = True
            oid = int(m['oid'])
            t = m['t']
            dl = m['dl']

        m = re.search(r_failed, line)
        if m != None:
            matched = True
            oid = int(m['oid'])
            dl = 1.0
            t = 2.0

        if matched != True:
            continue

        if args.start != None and oid < args.start:
            continue
        elif args.end != None and oid > args.end:
            continue

        rwin.append(float(t) < float(dl))
        while len(rwin) > args.window_size:
            rwin = rwin[1:]
        dsr = len(list(filter(lambda b: b, rwin))) / len(rwin)

        x.append(oid)
        y.append(dsr)

    plot_label = pretty_names[label]
    if add_labels != None:
        plot_label = '{}-{}'.format(plot_label, add_labels[0])
        add_labels = add_labels[1:]

    if args.date_runs == True:
        date_r = '^[A-Za-z]+ \d+ [0-9:]+'
        timestamp = re.search(date_r, log_lines[1])[0]
        plot_label = '{} ({})'.format(plot_label, timestamp)

    color2_idx = len(list(filter(lambda l: l == label, plotted)))

    plt.plot(x, y, label=plot_label, color=colors[label][color2_idx])
    x_limit = max(x_limit, len(y))
    plotted.append(label)

plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Windowed deadline satisfaction ratio')

if args.x_limit != None:
    x_limit = args.x_limit
xstart = args.start if args.start != None else -20
plt.xlim(-20, x_limit)
plt.ylim(0, 1.05)

plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.grid()


output_path = args.output
if os.path.isdir(output_path):
    output_path = os.path.join(output_path, 'dsr-offloads-windowed.pdf')

plt.savefig(output_path, format='pdf', dpi='figure', pad_inches=0.1, metadata={'Producer': str(args.paths)})
