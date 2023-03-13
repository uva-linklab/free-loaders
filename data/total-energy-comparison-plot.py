import argparse
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='output path',
                type=str, default='total-energy-comparison.pdf', dest='output')
ap.add_argument('--dsr', help='manually-specified DSRs',
                type=str, default=None, dest='dsrs')
ap.add_argument('--offload-limit', help='number of offloads to stop counting at',
                type=int, default=None, dest='limit')
ap.add_argument('paths', help='paths to log files (label,path)',
                nargs='+', type=str)
args = ap.parse_args()

# Scheduler algorithm.
x = []
# Total energy consumed.
y = []

r = 'finished task.*energy=(?P<energy>\d+\.\d+)'
labels_paths = map(lambda x: x.split(','), args.paths)
for [label, path] in labels_paths:
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    total_energy = 0
    offload_no = 0
    for line in log_lines:
        m = re.search(r, line)
        if m == None:
            continue

        task_execution_energy = float(m['energy'])
        total_energy += task_execution_energy

        offload_no += 1
        if args.limit != None and offload_no >= args.limit:
            print('Stopping counting excess offloads for scheduler {}.'.format(label))
            break

    total_energy = round(total_energy, 2)
    print('{} used {} mJ of energy'.format(label, total_energy))
    x.append(label)
    y.append(total_energy / 1000)

energy_color      = [176 / 255, 222 / 255, 120 / 255]
dark_energy_color = [139 / 255, 181 / 255, 88 / 255]
dsr_color         = [ 29 / 255, 120 / 255, 176 / 255]

# plt.ylim(0, 100)
# plt.xlabel('scheduler', fontsize='large')
# plt.ylabel('energy (J)')
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)

_fig, ax1 = plt.subplots()
# instead of text labels, map the x-axis to integers 0..
ax1.bar(list(map(lambda x: x-0.15, range(0,len(args.paths)))), y, zorder=0, color=energy_color, width=0.3)
# xticks are integers mapped to labels provided in the second argument...
ax1.set_xticks(list(map(lambda x: x, range(0, len(args.paths)))),
               labels=list(map(lambda s: s.split(',')[0], args.paths)),
               fontsize='large')
ax1.set_ylabel('energy (J)', fontsize='large', color=dark_energy_color)
ax1.set_ylim(0, 100)

if args.dsrs != None:
    dsrs = list(map(lambda s: float(s), args.dsrs.split(',')))
    ax2 = ax1.twinx()
    ax2.bar(list(map(lambda x: x+0.15, range(0,len(dsrs)))), dsrs, zorder=0, color=dsr_color, width=0.3)
    ax2.set_ylabel('DSR', fontsize='large', color=dsr_color)
    ax2.set_ylim(0, 1)

plt.grid(axis='y', zorder=-3)
plt.savefig(args.output, format='pdf', dpi='figure', bbox_inches='tight')
