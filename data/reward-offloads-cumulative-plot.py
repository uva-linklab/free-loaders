import argparse
import os.path
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='Output file path.',
                type=str, dest='output', default='reward-offloads-cumulative.pdf')
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=0)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('-f', '--initial-window', help='Assume a perfect initial DSR window',
                dest='initial_window', action='store_true', default=False)
ap.add_argument('--x-limit', help='Max offload no. to plot',
                dest='x_limit', type=int, action='store', default=None)
ap.add_argument('--date-runs', help='Append date labels to legends',
                dest='date_runs', action='store_true', default=False)
ap.add_argument('--override-labels', help='Force the labels in the plot',
                dest='override_labels', action='store', default=None)

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
}

pretty_names = {
    'rl': 'fReeLoaders',
    'load-bal': 'load balancer',
    'random': 'random',
    'time-wrr': 'performance-WRR',
    'heros': 'HEROS',
}

override_labels = args.override_labels.split(',')

def which_scheduler(log):
    scheduler_name = None
    r = 'using (?P<sched>[a-z0-9-]+) scheduler'
    for line in log:
        m = re.search(r, line)
        if m != None:
            scheduler_name = m['sched']
            break

    return scheduler_name

x_limit = 0
plotted = []
for (path, color) in zip(args.paths, range(0,10)):
    cumulative_reward_lines = ''
    with open(path, 'r') as fh:
        cumulative_reward_lines = fh.readlines()

    label = path

    y = []
    offset = 0
    last_met = 0
    failed = 0
    for line in cumulative_reward_lines:
        total_reward = float(line)
        y.append(total_reward)

    plot_label = ''
    if override_labels != None:
        plot_label = override_labels[0]
        plt.plot([i for i in range(0, len(y))], y, label=plot_label)
        override_labels = override_labels[1:]
    else:
        plot_label = pretty_names[label]
        if args.date_runs == True:
            date_r = '^[A-Za-z]+ \d+ [0-9:]+'
            timestamp = re.search(date_r, log_lines[1])[0]
            plot_label = '{} ({})'.format(plot_label, timestamp)

        color2_idx = len(list(filter(lambda l: l == label, plotted)))

        plt.plot([i for i in range(0, len(y))], y, label=plot_label, color=colors[label][color2_idx])
        plotted.append(label)
    x_limit = max(x_limit, len(y))
print('{}\n    total reward: {:.2f}'.format(plot_label, y[-1]))

plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Total reward')

if args.x_limit != None:
    x_limit = args.x_limit
plt.xlim(0, x_limit)
plt.ylim(0)

plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.grid()

output_path = args.output
if os.path.isdir(output_path):
    output_path = os.path.join(output_path, 'reward-offloads-cumulative.pdf')

plt.savefig(output_path, format='pdf', dpi='figure', pad_inches=0.1, metadata={'Producer': str(args.paths)})
