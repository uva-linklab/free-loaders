import argparse
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('paths', help='path to log files',
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

for path in args.paths:
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    sched_label = which_scheduler(log_lines)
    r = 'finished task.+energy=(?P<energy>\d+)'
    x = [0]
    y = [0]
    for line in log_lines:
        m = re.search(r, line)
        if m == None:
            continue

        energy = int(m['energy'])

        x.append(x[-1]+1)
        y.append(y[-1]+energy)

    plt.plot(x, y, label=pretty_names[sched_label], color=colors[sched_label])
    print('Total energy consumed by {}: {:.2f} J'.format(pretty_names[sched_label], y[-1] / 1000))

plt.legend(fancybox=True)

plt.xlabel('Number of offloads')
plt.ylabel('Total energy consumed')

plt.xlim(0, len(x))
plt.ylim(bottom=0)

plt.grid()

plt.savefig('/tmp/output.pdf', format='pdf', dpi='figure', pad_inches=0.1)
