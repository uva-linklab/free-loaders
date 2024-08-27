import argparse
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('path', help='path to log file',
                type=str)
args = ap.parse_args()

log_lines = ''
with open(args.path, 'r') as fh:
    log_lines = fh.readlines()

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

plt.plot(x, y)

plt.legend(fancybox=True)

plt.xlabel('Number of offloads')
plt.ylabel('Total energy consumed')

plt.xlim(0, len(x))
plt.ylim(bottom=0)

plt.grid()

plt.savefig('/tmp/output.pdf', format='pdf', dpi='figure', pad_inches=0.1)
