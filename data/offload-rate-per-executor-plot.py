import argparse
import re

import seaborn as sns
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='Output file path.',
                type=str, dest='output', default='offload-rate.pdf')
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=None)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('-w', '--window-size', help='Number of offloads in the averaging window',
                type=int, dest='window_size', default=25)

ap.add_argument('path', help='path to log file', type=str)

args = ap.parse_args()

pretty_names = {
    'rl': 'fReeLoaders',
    'load-bal': 'load balancer',
    'random': 'random',
    'heros': 'HEROS',
}

oid_executor_selection = []

def which_scheduler(log):
    scheduler_name = None
    r = 'using (?P<sched>[a-z0-9-]+) scheduler'
    for line in log:
        m = re.search(r, line)
        if m != None:
            scheduler_name = m['sched']
            break

    return scheduler_name

r = 'scheduled task.*offload_id=(?P<oid>\d+).*on executer_id=(?P<eid>\d+)'
plot_args = []
plotted = []
log_lines = ''
with open(args.path, 'r') as fh:
    log_lines = fh.readlines()

label = which_scheduler(log_lines)

x = []
y = []
rwin = [True for _i in range(0, args.window_size)]
offset = 0
last_met = 0
for line in log_lines:
    m = re.search(r, line)
    if m == None:
        continue

    oid = int(m['oid'])

    if args.start != None and args.start < oid:
        continue
    if args.end != None and args.end > oid:
        continue

    oid_executor_selection.append(int(m['eid']))

executor_count = 10
hmap = [[] for _i in range(executor_count)]
# For all the windows of the length window_size we can create...
for i in range(len(oid_executor_selection)):
    # Make the window that contains the EID of the executor selected to run the offloads.
    hmap_window = oid_executor_selection[i:i+args.window_size]
    # Place an average "rate" value: selections/offload count.
    for eid in range(executor_count):
        hmap[eid].append(float(hmap_window.count(eid)) / float(len(hmap_window)))

sns.heatmap(hmap, annot=False, xticklabels=200)

# plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Executor ID')
# plt.xlim(0, x[-1] if args.x_limit == None else args.x_limit)
# plt.ylim(0, 1)
# plt.gca().spines['right'].set_visible(False)
# plt.gca().spines['top'].set_visible(False)
# plt.grid()

plt.savefig(args.output, format='pdf', dpi='figure', pad_inches=0.1, metadata={'Producer': str(args.path)})
