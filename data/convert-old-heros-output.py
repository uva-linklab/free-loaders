#!/bin/env python

import argparse
import re

import matplotlib.pyplot as plt
import numpy

ap = argparse.ArgumentParser()
ap.add_argument('-o', '--output', help='Output file path.',
                type=str, dest='output', default='dsr-offloads.pdf')
ap.add_argument('--window-size', help='Number of samples in a window',
                type=int, dest='window', default=300)
ap.add_argument('-s', '--starting-offload', help='ID of the first offload to count',
                type=int, dest='start', default=0)
ap.add_argument('-e', '--ending-offload', help='ID of the last offload to count',
                type=int, dest='end', default=None)
ap.add_argument('-f', '--initial-window', help='Assume a perfect initial DSR window',
                dest='initial_window', action='store_true', default=False)
ap.add_argument('--x-limit', help='Max offload no. to plot',
                dest='x_limit', type=int, action='store', default=None)
ap.add_argument('paths', help='label,path to log file',
                nargs='+', type=str)

args = ap.parse_args()

r = 'deadlines_met=(?P<met>\d+).*finished_tasks=(?P<finished>\d+).*failed_tasks=(?P<failed>\d+)'
r2 = 'finished task.*offload_id=(?P<oid>\d+), task_id=(?P<tid>\d+).*time\(ms\)=(?P<t>\d+\.\d+)'
eligible_re = 'eligible for task_id=(?P<tid>\d+)'
selecting_re = 'selecting executor_id=(?P<eid>\d+)'

eid = 999
tid = 999
log_lines = ''
with open(args.paths[0], 'r') as fh:
    log_lines = fh.readlines()

oid = 0
for line in log_lines:
    m = re.search(eligible_re, line)
    if m != None:
        tid = int(m['tid'])

    else:
        m = re.search(selecting_re, line)
        if m == None:
            continue

        eid = int(m['eid'])

        print('scheduled task offload_id={}, task_id={}, on executer_id={}'.format(oid, tid, eid))
        oid += 1

