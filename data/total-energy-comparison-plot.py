import argparse
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='output path',
                type=str, default='total-energy-comparison.pdf', dest='output')
ap.add_argument('paths', help='paths to log files (label,path)',
                nargs='+', type=str)
args = ap.parse_args()

# Scheduler algorithm.
x = []
# Total energy consumed.
y = []

r = 'energy=(?P<energy>\d+\.\d+)'
labels_paths = map(lambda x: x.split(','), args.paths)
for [label, path] in labels_paths:
    log_lines = ''
    with open(path, 'r') as fh:
        log_lines = fh.readlines()

    total_energy = 0
    for line in log_lines:
        m = re.search(r, line)
        if m == None:
            continue

        task_execution_energy = float(m['energy'])
        total_energy += task_execution_energy

    total_energy = round(total_energy, 2)
    print('{} used {} mJ of energy'.format(label, total_energy))
    x.append(label)
    y.append(total_energy / 1000)

barlist = plt.bar(x, y, zorder=3)

for bar in barlist:
    bar.set_color([176 / 255, 222 / 255, 120 / 255])

plt.ylim(0)
plt.xlabel('scheduler')
plt.ylabel('energy (J)')
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.grid(axis='y', zorder=0)
plt.savefig(args.output, format='pdf', dpi='figure', bbox_inches='tight')
