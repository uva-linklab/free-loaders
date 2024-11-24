import argparse
import os.path
import re

import matplotlib.figure as pltf
import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='output path',
                type=str, default='/tmp', dest='output')
ap.add_argument('--dsr', help='manually-specified DSRs',
                type=str, default=None, dest='dsrs')
ap.add_argument('--offload-limit', help='number of offloads to stop counting at',
                type=int, default=None, dest='limit')
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

xlabels = []
dsrs = []
energy_consumptions = []

r = 'finished task.*energy=(?P<energy>\d+\.\d+)'
r_dsr = 'dsr=(?P<dsr>\d+\.\d+)'
for path in args.paths:
    dsrs.append(0.0)
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    total_energy = 0
    offload_no = 0
    for line in log_lines:
        m = re.search(r, line)
        if m != None:
            task_execution_energy = float(m['energy'])
            total_energy += task_execution_energy

            offload_no += 1
            if args.limit != None and offload_no >= args.limit:
                print('Stopping counting excess offloads for scheduler {}.'.format(label))
                break
        else:
            m = re.search(r_dsr, line)
            if m != None:
                dsrs[-1] = float(m['dsr'])

    scheduler_name = which_scheduler(log_lines)
    xlabels.append(pretty_names[scheduler_name])
    total_energy = round(total_energy, 2)
    print('{} used {:.2f} mJ of energy'.format(scheduler_name, total_energy))
    x.append(pretty_names[scheduler_name])
    y.append(total_energy / 1000)
    energy_consumptions.append(total_energy / 1000)

energy_color      = [176 / 255, 222 / 255, 120 / 255]
dark_energy_color = [139 / 255, 181 / 255,  88 / 255]
dsr_color         = [ 29 / 255, 120 / 255, 176 / 255]

# plt.ylim(0, 100)
# plt.xlabel('scheduler', fontsize='large')
# plt.ylabel('energy (J)')
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)

# w, h = pltf.figaspect(.5)
# fig, ax1 = plt.subplots(figsize=(w,h,))

_fig, ax1 = plt.subplots()
# instead of text labels, map the x-axis to integers 0..
ax1.bar(list(map(lambda x: x, range(0,len(args.paths)))),
    [11.76, 27.53, 4.93, 36.07, 35.40], zorder=100, color=energy_color)
# xticks are integers mapped to labels provided in the second argument...
ax1.set_xticks(list(map(lambda x: x, range(0, len(args.paths)))),
        labels=xlabels)
ax1.set_ylabel('energy (J)', fontsize='large')
# ax1.set_ylim(0, 40)
yticks = [x * 10 for x in range(0, 5)]
ax1.set_yticks(yticks,
               labels=['{} J'.format(x) for x in yticks])

plt.grid(axis='y', zorder=-100)

plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)

# ax2 = ax1.twinx()
# ax2.bar(list(map(lambda x: x+0.15, range(0,len(dsrs)))), dsrs, zorder=100, color=dsr_color, width=0.3)
# ax2.set_ylabel('DSR', fontsize='large', color=dsr_color)
# ax2.set_ylim(0, 1)

output_path = args.output
if os.path.isdir(output_path) == True:
    output_path = os.path.join(output_path, 'total-energy-comparison.pdf')

plt.savefig(output_path, format='pdf', dpi='figure', bbox_inches='tight')
