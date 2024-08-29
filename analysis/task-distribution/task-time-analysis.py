import argparse
import itertools
import re
import statistics
from tabulate import tabulate

ap = argparse.ArgumentParser(description='Task run-time analyzer')
ap.add_argument('-e', '--executor-count', help='specify no. of executors',
                type=int, default=10, dest='num_executors')
ap.add_argument('-es', '--epsilon-start', help='starting epsilon value',
                type=float, default=0.0, dest='epsilon_start')
ap.add_argument('-ee', '--epsilon-end', help='ending epsilon value',
                type=float, default=1.0, dest='epsilon_end')
ap.add_argument('-ois', '--offload-id-start', help='starting offload_id',
                type=int, default=0, dest='start_offload_id')
ap.add_argument('-oie', '--offload-id-end', help='ending offload_id',
                type=int, default=500000, dest='end_offload_id') # setting default end offload to a large number
ap.add_argument('--percent', help='Show std. dev. as percent values',
                dest='percent', default=False, action='store_true')
ap.add_argument('--importable', help='Print the table less fancy for copying',
                dest='importable', default=False, action='store_true')

ap.add_argument('dataset', help='dataset to calculate',
                type=str, choices=['runtime', 'runtime-stdev', 'slack', 'dsr', 'energy'])
ap.add_argument('log_file', help='Log file to parse')

args = ap.parse_args()

DEVICES = ["nano", "rpi3", "rpi3", "rpi4", "rpi4", "rpi4", "rpi4", "rpi4", "tx2", "desktop"]
POWER   = [1.33,   1.07,   1.07,   1.8,    1.8,    1.8,    1.8,    1.8,    4.01,  70.9]

# TID -> (EID -> [slack times])
task_to_executor_mapping = {}

def raw_or_imp(a, raw, fancy):
    if a.importable == True:
        return raw
    else:
        return fancy

# open log file
regexp = '.*finished task.*task_id=(?P<tid>\d+).*executer_id=(?P<eid>\d+).*time\(ms\)=(?P<t>\d+|\d+\.\d+).*deadline=(?P<dl>\d+|\d+\.\d+).*energy=(?P<energy>\d+\.\d+)'
with open(args.log_file, 'r') as f:
    data = f.read()
    for m in re.findall(regexp, data):
        eid = int(m[1])
        tid = int(m[0])
        t_exec = float(m[2])
        t_dl = float(m[3])
        energy = float(m[4])

        task_slack_times = task_to_executor_mapping.get(tid, {x: [] for x in range(0, 10)})
        ex_slack_times = task_slack_times.get(eid, [])

        if args.dataset.startswith('runtime'):
            ex_slack_times.append(round(t_exec, 1))
        elif args.dataset.startswith('slack') or args.dataset == 'dsr':
            ex_slack_times.append(round(t_dl - t_exec, 1))
        elif args.dataset == 'energy':
            if t_dl - t_exec > 0:
                ex_slack_times.append(energy)

        task_slack_times[eid] = ex_slack_times
        task_to_executor_mapping[tid] = task_slack_times

# Transform times into averages or stdev.
rows = []
for (tid, eid_slack_times) in task_to_executor_mapping.items():
    row = [tid]
    it = list(eid_slack_times.items())
    it.sort(key=lambda x: x[0])
    for (eid, slack_times) in it:
        # Map to standard deviations.
        if args.dataset.endswith('-stdev'):
            if len(slack_times) <= 1:
                row.append(raw_or_imp(args,
                                      0,
                                      '---'))
            else:
                avg = sum(slack_times) / len(slack_times)
                stdev = statistics.stdev(slack_times)
                if args.percent == False:
                    row.append(raw_or_imp(args,
                                          stdev,
                                          '{} ms'.format(round(stdev, 1))))
                else:
                    row.append(raw_or_imp(args,
                                          stdev / avg,
                                          '± {}%'.format(round(stdev / avg * 100, 1))))

        # Map to averages.
        else:
            if len(slack_times) == 0:
                row.append(raw_or_imp(args,
                                      0,
                                      '---'))
            else:
                # Handle DSR data.
                if args.dataset == 'dsr':
                    dsr = len(list(filter(lambda st: st >= 0.0, slack_times))) / len(slack_times)
                    row.append(raw_or_imp(args,
                                          dsr,
                                          '{:.2f} %'.format(round(dsr * 100, 1))))
                elif args.dataset == 'energy':
                    row.append(raw_or_imp(args,
                                          sum(slack_times) / len(slack_times),
                                          '{:.2f} J'.format(round(sum(slack_times) / len(slack_times), 2))))
                else:
                    avg = sum(slack_times) / len(slack_times)
                    row.append(raw_or_imp(args,
                                          avg,
                                          '{:.1f} ms'.format(round(avg, 1))))

    rows.append(row)

rows.sort(key=lambda r: r[0])

# Add separating lines.
if args.importable == False:
    from tabulate import SEPARATING_LINE
    task_set_rows = [rows[i:i+10] + [SEPARATING_LINE] for i in range(0, len(rows), 10)]
    rows = []
    for task_set in task_set_rows:
        rows += task_set

import itertools
devices = ['{}-{}'.format(n, name) for (n, name) in zip(itertools.count(), DEVICES)]
headers = ["TaskId"] + DEVICES

alignment = ['right' for _i in range(0, len(rows[0]))]

if args.importable == True:
    print(tabulate(rows, headers=headers, tablefmt='tsv'))
else:
    print(tabulate(rows, headers=headers, colalign=tuple(alignment)))
