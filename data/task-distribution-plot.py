import argparse
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('--by-id',
                help='show individual executor IDs',
                dest='by_id', action='store_true')
ap.add_argument('-s', '--starting-offload',
                help='ID of the first offload to count',
                type=int, dest='start', default=0)
ap.add_argument('-e', '--ending-offload',
                help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('-o', '--output-path',
                help='Path to save the figure to',
                type=str, dest='output', default='/tmp/task-distribution.pdf')
ap.add_argument('--y-limit', help='Maximum y-axis value',
                type=int, dest='y_lim', default=None)
ap.add_argument('path', help='path to log file',
                type=str)

args = ap.parse_args()

log_lines = ''
with open(args.path, 'r') as fh:
    log_lines = fh.readlines()

r = 'scheduled task.* on executer_id=(?P<eid>\d+)'
x = []
if args.by_id == False:
    x = ['nano',
         'rpi3a+',
         'rpi4b',
         'tx2',
         'desktop']
else:
    x = [str(x) for x in range(0,10)]

y = [0 for _i in range(0, len(x))]
offload_no = 0
for line in log_lines:
    m = re.search(r, line)
    if m == None:
        continue

    offload_no += 1

    if offload_no < args.start:
        continue
    elif args.end != None and args.end < offload_no:
        break

    eid = int(m['eid'])
    if args.by_id == False:
        if 1 <= eid and eid <= 2:
            eid = 1
        elif 3 <= eid and eid <= 7:
            eid = 2
        elif eid == 8:
            eid = 3
        elif eid == 9:
            eid = 4

    y[eid] += 1

print(y)


plt.bar(x, y, zorder=3)
plt.xticks(rotation=45, ha='right', fontsize='xx-large')
plt.xlabel('executor')
plt.ylabel('No. of offloads')

if args.y_lim != None:
    plt.ylim(0, args.y_lim)

plt.grid(axis='y', zorder=0)
plt.savefig(args.output, format='pdf', dpi='figure', bbox_inches='tight')
