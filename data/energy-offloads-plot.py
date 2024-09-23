import argparse
import os.path
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=None)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('-o', '--output', help='path to output',
                default='/tmp')
ap.add_argument('--x-limit', help='x-axis max value',
                type=int, dest='x_limit', default=None)
ap.add_argument('--date-runs', help='Append date labels to legends',
                dest='date_runs', action='store_true', default=False)
ap.add_argument('paths', help='path to log files',
                nargs='+', type=str)
args = ap.parse_args()

colors = {
    'rl': [[26 / 255, 121 / 255, 172 / 255],
           [137 / 255, 204 / 255, 240 / 255],
           [183 / 255, 218 / 255, 237 / 255]],
    'load-bal': [28 / 255, 160 / 255, 63 / 255],
    'random': [217 / 255, 28 / 255, 44 / 255],
    'heros': [[111 / 255, 166 / 255, 17 / 255],
              [170 / 255, 227 / 255, 73 / 255]],
}

pretty_names = {
    'rl': 'fReeLoaders',
    'load-bal': 'load balancer',
    'random': 'random',
    'heros': 'HEROS',
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

plotted = []
x_lim = args.x_limit
for path in args.paths:
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    sched_label = which_scheduler(log_lines)
    r = 'finished task.+offload_id=(?P<oid>\d+).+energy=(?P<energy>\d+\.\d+)'
    x = [0]
    y = [0]
    e = []
    for line in log_lines:
        m = re.search(r, line)
        if m == None:
            continue

        oid = int(m['oid'])

        if args.start != None and oid < args.start:
            continue
        if args.end != None and oid >=args.end:
            continue

        energy = float(m['energy'])

        x.append(x[-1]+1)
        y.append(y[-1]+energy)
        e.append(energy)

        if args.x_limit == None:
            if x_lim == None:
                x_lim = len(x)
            else:
                x_lim = max(x_lim, len(x))

    plot_label = pretty_names[sched_label]
    if args.date_runs == True:
        date_r = '^[A-Za-z]+ \d+ [0-9:]+'
        timestamp = re.search(date_r, log_lines[1])[0]
        plot_label = '{} ({})'.format(plot_label, timestamp)

    color2_idx = len(list(filter(lambda l: l == sched_label, plotted)))
    plt.plot(x, y, label=plot_label, color=colors[sched_label][color2_idx])
    plotted.append(sched_label)
    print('Total energy consumed by {}: {:.2f} J; Avg. rate: {} J/offload'.format(
        pretty_names[sched_label],
        y[-1],
        round(sum(e) / len(e), 2)))

plt.legend(fancybox=True)

plt.xlabel('Number of offloads')
plt.ylabel('Total energy consumed')

plt.xlim(0, x_lim)
plt.ylim(bottom=0)

plt.grid()

output_path = args.output
if os.path.isdir(output_path) == True:
    output_path = os.path.join(output_path, 'energy-offloads.pdf')

plt.savefig(output_path, format='pdf', dpi='figure', pad_inches=0.1)
