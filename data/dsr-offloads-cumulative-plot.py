import argparse
import os.path
import re

import matplotlib.pyplot as plt
import matplotlib.figure as pltf
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='Output file path.',
                type=str, dest='output', default='/tmp')
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=0)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('-f', '--initial-window', help='Assume a perfect initial DSR window',
                dest='initial_window', action='store_true', default=False)
ap.add_argument('--x-limit', help='Max offload no. to plot',
                dest='x_limit', type=int, action='store', default=None)
ap.add_argument('--use-markers', help='Place markers on plots',
                dest='use_markers', type=str, action='store', default=None)
ap.add_argument('--append-labels', help='Apply additional labeling to legend',
                dest='append_labels', type=str, action='store', default=None)
ap.add_argument('--date-runs', help='Append date labels to legends',
                dest='date_runs', action='store_true', default=False)
ap.add_argument('--override-labels', help='Force the labels in the plot',
                dest='override_labels', action='store', default=None)
ap.add_argument('--legend-order', help='Force the ordering of the legend',
                dest='legend_order', action='store', default=None)
ap.add_argument('--dir-name-runs', help='Append containing directory names to legend',
                dest='dir_name_runs', action='store_true', default=False)

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

override_labels = None
if args.override_labels != None:
    override_labels = args.override_labels.split(',')

use_markers = None
if args.use_markers != None:
    use_markers = args.use_markers.split(',')
else:
    use_markers = ['' for _i in range(0, len(args.paths))]

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
# fig.subplots_adjust(left=.1, right=0.98, top=0.97, bottom=0.12)

r = 'deadlines_met=(?P<met>\d+).*finished_tasks=(?P<finished>\d+).*failed_tasks=(?P<failed>\d+)'
r2 = 'finished task.*offload_id=(?P<oid>\d+), task_id=(?P<tid>\d+).*time\(ms\)=(?P<t>\d+\.\d+)'
r3 = 'failed task.*offload_id'
x_limit = 0
plotted = []
skipped = 0
met_offset = 0
proc_offset = 0
add_labels = args.append_labels.split(',') if args.append_labels != None else None
for (path, color) in zip(args.paths, range(0,10)):
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    label = which_scheduler(log_lines)

    x = []
    y = []
    offset = 0
    last_met = 0
    failed = 0
    for line in log_lines:
        m = re.search(r, line)
        if m == None:
            m = re.search(r2, line)

            if m == None:
                m = re.search(r3, line)

                if m == None:
                    continue
                failed += 1

            continue

        if skipped < args.start:
            skipped += 1
            # print('skipped  {}'.format(skipped))
            continue
        elif skipped == args.start:
            met_offset = int(m['met'])
            proc_offset = int(m['finished']) + int(m['failed'])
            skipped += 1

        met = int(m['met']) - met_offset
        finished = int(m['finished'])
        # failed = int(m['failed'])
        processed = finished + failed - proc_offset

        # print('{} / {}'.format(met, processed))

        x.append(processed)
        y.append(1.0 if processed <= 0 else met / processed)

        last_met = met

    # Order the points.
    points = [(x,y,) for (x,y,) in zip(x,y)]
    points.sort()
    x = [x for (x,y,) in points]
    y = [y for (x,y,) in points]

    skipped = 0
    plot_label = ''
    if override_labels != None:
        plot_label = override_labels[0]
        ax.plot(x, y, label=plot_label)
        override_labels = override_labels[1:]
    else:
        plot_label = pretty_names[label]
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

        color2_idx = len(list(filter(lambda l: l == label, plotted)))

        ax.plot(x, y,
                label=plot_label,
                color=colors[label][color2_idx],
                marker=use_markers[0],
                markevery=250,
                # markersize=2.0
                )
        plotted.append(label)
        use_markers = use_markers[1:]

    x_limit = max(x_limit, len(y))
    print('{}\n    DSR: {:.2f}%'.format(plot_label, y[-1] * 100))

ax.set_xlabel('Number of offloads', fontsize=16)
ax.set_ylabel('Cumulative deadline satisfaction ratio', fontsize=16)

if args.legend_order != None:
    handles, labels = plt.gca().get_legend_handles_labels()
    order = [int(x) for x in args.legend_order.split(',')]
    plt.legend([handles[i] for i in order],
               [labels[i] for i in order])
else:
    ax.legend(fancybox=True, reverse=True, fontsize=12)

# plt.axvline(500, ymin=0, ymax=2.0, linestyle=':', color=[0.0, 0.0, 0.0], linewidth=3.0)

if args.x_limit != None:
    x_limit = args.x_limit
ax.set_xlim(0, x_limit)
ax.set_ylim(0, 1.0)
ax.tick_params(labelsize=12)

plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.grid()

output_path = args.output
if os.path.isdir(output_path):
    output_path = os.path.join(output_path, 'dsr-offloads-cumulative.pdf')

plt.savefig(output_path, format='pdf', dpi='figure', bbox_inches='tight', metadata={'Producer': str(args.paths)})
