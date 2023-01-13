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

r = 'deadlines_met=(?P<met>\d+).*finished_tasks=(?P<finished>\d+).*failed_tasks=(?P<failed>\d+)'
x = [0]
y = [1]
for line in log_lines:
    m = re.search(r, line)
    if m == None:
        continue

    met = int(m['met'])
    finished = int(m['finished'])
    failed = int(m['failed'])

    x.append(finished)
    y.append(met / (finished + failed))

plt.plot(x, y)

plt.legend(fancybox=True)
plt.xlabel('Number of offloads')
plt.ylabel('Deadline satisfaction ratio')
plt.xlim(0, 10000)
plt.ylim(0, 1)
plt.grid()
plt.savefig('/tmp/output.pdf', format='pdf', dpi='figure', pad_inches=0.1)
