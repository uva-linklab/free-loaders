import argparse
import os.path
import re

import matplotlib.figure as pltf
import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='output path',
                type=str, default='/tmp', dest='output')
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=None)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('--y-limit', help='Set the y-limit of the y-axis in joules.',
                type=int, dest='y_limit', default=None)
ap.add_argument('--append-labels', help='Apply additional labeling to legend',
                dest='append_labels', type=str, action='store', default=None)
ap.add_argument('--manual-adjust', help="Apply manual adjustment to plot's T/B/L/R",
                type=str, dest='manual_adjust', default=None)
ap.add_argument('paths', help='paths to log files',
                nargs='+', type=str)
args = ap.parse_args()

# Scheduler algorithm.
x = []
# Total energy consumed.
y = []

pretty_names = {
    'rl': 'fReeLoaders',
    'load-bal': '''load
balancer''',
    'random': 'random',
    'heros': 'HEROS',
    'time-wrr': 'WRR',
    'adpt-lb-v1': '''energy-
priority''',
    'adpt-lb-v3': '''performance-
priority''',
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

xlabels = []
dsrs = []
energy_consumptions = []
add_labels = args.append_labels.split(',') if args.append_labels != None else None

w, h = pltf.figaspect(.6)
fig, ax1 = plt.subplots(figsize=(w,h,))
if args.manual_adjust != None:
    d = [float(d) for d in args.manual_adjust.split(',')]
    fig.subplots_adjust(top=d[0], bottom=d[1], left=d[2], right=d[3])

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

        oid = int(m['oid'])

        if args.start != None and oid < args.start:
            continue
        if args.end != None and oid > args.end:
            break

        completed_oids.add(oid)
    common_completed_oids = common_completed_oids.intersection(completed_oids)

print('Common completed offloads: {}'.format(len(common_completed_oids)))

to_plot = []
plotted = []
y_lim = 0
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

        if oid not in common_completed_oids:
            continue

        if args.start != None and oid < args.start:
            continue
        if args.end != None and oid >= args.end:
            continue

        energy = float(m['energy'])

        x.append(x[-1]+1)
        y.append(y[-1]+energy)
        e.append(energy)

    energy_consumptions.append(y[-1] / 1000)

    if add_labels != None:
        xlabels.append(f'{pretty_names[sched_label]}\n{add_labels[0]}')
        add_labels = add_labels[1:]
    else:
        xlabels.append(pretty_names[sched_label])

    print('Total energy consumed by {}: {:.2f} J; Avg. rate: {} J/offload'.format(
        pretty_names[sched_label],
        y[-1],
        round(sum(e) / len(e), 2)))

# Last is first, so most important shows up closer to the left.
energy_consumptions.reverse()
xlabels.reverse()

energy_color      = [176 / 255, 222 / 255, 120 / 255]
dark_energy_color = [139 / 255, 181 / 255,  88 / 255]
dsr_color         = [ 29 / 255, 120 / 255, 176 / 255]

plt.grid(axis='y')
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)

# Instead of text labels, map the x-axis to integers 0..
ax1.set_axisbelow(True)
# Set separation distance for ticks and bars.
bar_dist = 0.7
ax1.bar(list(map(lambda x: x * bar_dist, range(0, len(args.paths)))),
        energy_consumptions,
        width=bar_dist * 0.6,
    color=energy_color)
# xticks are integers mapped to labels provided in the second argument...
ax1.set_xticks(list(map(lambda x: x * bar_dist, range(0, len(args.paths)))),
               labels=xlabels,
               fontsize=12)
ax1.set_xlim(0 - bar_dist / 2, bar_dist * len(args.paths) - bar_dist / 2)
ax1.set_ylabel('Energy usage (J)', fontsize=16)

yticks = None
if args.y_limit == None:
    # Small complexity to make the y-ticks scale correctly.
    # Discover what the order of magnitude of the greatest value we deal with is.
    oom = len(str(int(max(energy_consumptions)))) - 1
    oom = 2
    # Use it to determine how many ticks we will need in counting up
    # in the same increment matching its order of magnitude.
    # Plus one for the 0 tick, plus one to exceed the greatest value.
    num_yticks = int(max(energy_consumptions) / pow(10, oom-1)) + 1 + 1
    yticks = [x * pow(10, oom-1) for x in range(0, num_yticks)]
else:
    num_yticks = int(args.y_limit / 10000) + 1
    yticks = [x * 10 for x in range(0, num_yticks)]
ax1.set_ylim(0, (max(energy_consumptions) + 10))
ax1.set_yticks(yticks,
               labels=['{} kJ'.format(x) for x in yticks],
               fontsize=14)

plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)

output_path = args.output
if os.path.isdir(output_path) == True:
    output_path = os.path.join(output_path, 'total-energy-comparison.pdf')

plt.savefig(output_path, format='pdf', dpi='figure', bbox_inches='tight')
