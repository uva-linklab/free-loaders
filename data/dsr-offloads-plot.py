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
ap.add_argument('-f', '--initial-window', help='Assume a perfect initial DSR window',
                dest='initial_window', action='store_true', default=False)
ap.add_argument('--x-limit', help='Max offload no. to plot',
                dest='x_limit', type=int, action='store', default=None)
ap.add_argument('paths', help='path to log file',
                nargs='+', type=str)

args = ap.parse_args()

colors = {
    'rl': [26 / 255, 121 / 255, 172 / 255],
    'load-bal': [28 / 255, 160 / 255, 63 / 255],
    'random': [217 / 255, 28 / 255, 44 / 255],
    'heros': [111 / 255, 166 / 255, 17 / 255],
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

r = 'deadlines_met=(?P<met>\d+).*finished_tasks=(?P<finished>\d+).*failed_tasks=(?P<failed>\d+)'
r2 = 'finished task.*offload_id=(?P<oid>\d+), task_id=(?P<tid>\d+).*time\(ms\)=(?P<t>\d+\.\d+)'
for (path, color) in zip(args.paths, range(0,10)):
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    label = which_scheduler(log_lines)

    RL_MEMORY_SKIP_TOTAL = 0
    if label == 'fReeLoaders':
        RL_MEMORY_SKIP_TOTAL= 0
    elif label == 'fReeLoaders (more training)':
        RL_MEMORY_SKIP_TOTAL = 0
    elif label == 'fReeLoaders (-100 reward)':
        RL_MEMORY_SKIP_TOTAL = 0

    x = []
    y = []
    offset = 0
    last_met = 0
    rl_memory_skip = 0
    rl_memory_met = 0
    rl_memory_finished = 0
    rl_memory_failed = 0
    for line in log_lines:
        m = re.search(r, line)
        if m == None:
            m = re.search(r2, line)

            if m == None:
                continue

            # See if this one failed due to network conditions.
            t = float(m['t'])
            oid = int(m['oid'])
            if oid > 3000 and t > 80000:
                offset += 1
                print('not counting long time {} for task ID {}'.format(t, m['tid']))
            continue


        # Skip over the offloads where the memory was filling for the RL scheduler.
        if 'fReeLoaders' in label and rl_memory_skip < RL_MEMORY_SKIP_TOTAL:
            rl_memory_skip += 1
            if rl_memory_skip == RL_MEMORY_SKIP_TOTAL:
                # Set the offset nos.
                rl_memory_met = int(m['met'])
                rl_memory_finished = int(m['finished'])
                rl_memory_failed = int(m['failed'])
            continue

        met = int(m['met']) - rl_memory_met
        finished = int(m['finished']) - rl_memory_finished - offset
        failed = int(m['failed']) - rl_memory_failed
        processed = finished + failed - offset

        x.append(processed)
        y.append(met / processed)

        last_met = met

    plt.plot(x, y, label=pretty_names[label], color=colors[label])

plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Deadline satisfaction ratio')
plt.xlim(0, x[-1] if args.x_limit == None else args.x_limit)
plt.ylim(0, 1)
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.grid()
plt.savefig(args.output, format='pdf', dpi='figure', pad_inches=0.1)
