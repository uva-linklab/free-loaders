import argparse
import os.path
import re

import matplotlib.pyplot as plt
import matplotlib.figure as pltf
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
ap.add_argument('--append-labels', help='Apply additional labeling to legend',
                dest='append_labels', type=str, action='store', default=None)
ap.add_argument('--date-runs', help='Append date labels to legends',
                dest='date_runs', action='store_true', default=False)
ap.add_argument('--dir-name-runs', help='Append containing directory names to legend',
                dest='dir_name_runs', action='store_true', default=False)
ap.add_argument('paths', help='path to log files',
                nargs='+', type=str)
args = ap.parse_args()

colors = {
    'rl': [[26 / 255, 121 / 255, 172 / 255],
           [137 / 255, 204 / 255, 240 / 255],
           [183 / 255, 218 / 255, 237 / 255]],
    'load-bal': [[199 / 255, 157 / 255, 250 / 255]],
    'random': [[217 / 255, 28 / 255, 44 / 255]],
    'time-wrr': [[252 / 255, 186 / 255,   3 / 255]],
    'heros': [[40 / 255, 100 / 255, 20 / 255],
              [80 / 255, 150 / 255, 40 / 255],
              [120 / 255, 200 / 255, 60 / 255],
              [170 / 255, 227 / 255, 90 / 255],
              [200 / 255, 255 / 255, 120 / 255]],
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

    if scheduler_name == 'heros-is':
        scheduler_name = 'heros'

    return scheduler_name

w, h = pltf.figaspect(.6)
fig, ax = plt.subplots(figsize=(w,h,))
fig.subplots_adjust(top=0.95)

common_completed_oids = set([x for x in range(99999)])
# Find out which OIDs were successfully completed.
for path in args.paths:
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    r = 'finished task.+offload_id=(?P<oid>\d+).+energy=(?P<energy>\d+\.\d+)'
    completed_oids = set()
    for line in log_lines:
        m = re.search(r, line)
        if m == None:
            continue

        completed_oids.add(int(m['oid']))
    common_completed_oids = common_completed_oids.intersection(completed_oids)

print('Common completed offloads: {}'.format(len(common_completed_oids)))

to_plot = []
plotted = []
x_lim = args.x_limit
y_lim = 0
add_labels = args.append_labels.split(',') if args.append_labels != None else None
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

        # if oid not in common_completed_oids:
        #     continue

        if args.start != None and oid < args.start:
            continue
        if args.end != None and oid >=args.end:
            continue
        if args.x_limit != None and oid >= args.x_limit:
            continue

        energy = float(m['energy'])

        x.append(oid)
        y.append(y[-1]+(energy / 1000))
        e.append(energy)

        if args.x_limit == None:
            if x_lim == None:
                x_lim = len(x)
            else:
                x_lim = max(x_lim, len(x))

    plot_label = pretty_names[sched_label]
    if add_labels != None:
        plot_label = '{} {}'.format(plot_label, add_labels[0])
        add_labels = add_labels[1:]

    if args.date_runs == True:
        date_r = '^[A-Za-z]+ \d+ [0-9:]+'
        timestamp = re.search(date_r, log_lines[1])[0]
        plot_label = '{} ({})'.format(plot_label, timestamp)

    if args.dir_name_runs == True:
        (_p1, containing_dir_name) = os.path.split(os.path.split(path)[0])
        plot_label = '{} ({})'.format(plot_label, containing_dir_name)

    color2_idx = len(list(filter(lambda l: l == sched_label, plotted)))
    y_lim = max(y_lim, y[-1])
    plt.plot(x, y, label=plot_label, color=colors[sched_label][color2_idx])
    plotted.append(sched_label)
    print('Total energy consumed by {}: {:.2f} J; Avg. rate: {} J/offload'.format(
        pretty_names[sched_label],
        y[-1],
        round(sum(e) / len(e), 2)))

plt.legend(fancybox=True)

plt.xlabel('Number of offloads', fontsize=16)
plt.ylabel('Total energy consumed', fontsize=16)

plt.xlim(0, x_lim)
plt.ylim(bottom=0)
ax.tick_params(labelsize=12)

plt.grid()

output_path = args.output
if os.path.isdir(output_path) == True:
    output_path = os.path.join(output_path, 'energy-offloads.pdf')

plt.savefig(output_path, format='pdf', dpi='figure', bbox_inches='tight')
